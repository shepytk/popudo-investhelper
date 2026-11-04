"""One-at-a-time work queue with bounded retries, lease expiry and dead-letter state."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import ExternalIdentifier, IngestionJob
from app.observability import audit
from app.modules.ingestion.contracts import SnapshotStore
from app.modules.ingestion.pipeline import import_batch
from app.modules.ingestion.providers import ProviderRateLimited, provider_from_environment


def naive_utc() -> datetime:
    # SQLAlchemy's legacy timestamps use timezone-naive UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue(db: Session, company_id: int, provider: str, subject: str, *, when: datetime | None = None) -> IngestionJob:
    identifier = db.scalar(select(ExternalIdentifier).where(
        ExternalIdentifier.company_id == company_id,
        ExternalIdentifier.provider == provider,
        ExternalIdentifier.provider_company_id == subject,
    ))
    if identifier is None:
        raise ValueError("Issuer/provider mapping has not been verified")
    existing = db.scalar(select(IngestionJob).where(
        IngestionJob.company_id == company_id,
        IngestionJob.provider == provider,
        IngestionJob.subject == subject,
        IngestionJob.state.in_(("pending", "running", "retry")),
    ).limit(1))
    if existing:
        return existing
    job = IngestionJob(
        company_id=company_id, provider=provider, subject=subject,
        state="pending", next_run_at=when or naive_utc(),
        attempts=0, max_attempts=3,
    )
    db.add(job)
    db.flush()
    return job


def claim(db: Session, *, now: datetime | None = None) -> IngestionJob | None:
    now = now or naive_utc()
    stmt = (
        select(IngestionJob)
        .where(or_(
            (IngestionJob.state.in_(("pending", "retry"))) & (IngestionJob.next_run_at <= now),
            (IngestionJob.state == "running") & (IngestionJob.started_at < now - timedelta(minutes=15)),
        ))
        .order_by(IngestionJob.next_run_at, IngestionJob.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    job = db.scalar(stmt)
    if not job:
        return None
    job.state = "running"
    job.started_at = now
    job.attempts += 1
    db.flush()
    return job


def work_one(session_factory: sessionmaker, store: SnapshotStore) -> bool:
    with session_factory.begin() as db:
        job = claim(db)
        if job is None:
            return False
        job_id, company_id, provider_name, subject = job.id, job.company_id, job.provider, job.subject
    try:
        provider = provider_from_environment(provider_name)
        batch = provider.collect(subject)
        if batch.evidence.provider != provider_name:
            raise ValueError("Provider identity mismatch")
        with session_factory.begin() as db:
            identifier = db.scalar(select(ExternalIdentifier).where(
                ExternalIdentifier.company_id == company_id,
                ExternalIdentifier.provider == provider_name,
                ExternalIdentifier.provider_company_id == subject,
            ))
            if identifier is None:
                raise ValueError("Unverified provider identifier")
            import_batch(db, company_id, batch, store)
            job = db.get(IngestionJob, job_id)
            job.state = "succeeded"
            job.completed_at = naive_utc()
            job.last_error = None
            audit("ingestion.succeeded", job_id=job_id, company_id=company_id,
                  provider=provider_name, state="succeeded", attempts=job.attempts,
                  facts_imported=len(batch.facts), quotes_imported=len(batch.quotes),
                  fx_imported=len(batch.fx_rates), listings_imported=len(batch.listings))
    except Exception as exc:
        with session_factory.begin() as db:
            job = db.get(IngestionJob, job_id)
            job.last_error = f"{type(exc).__name__}: {str(exc)[:300]}"
            if job.attempts >= job.max_attempts:
                job.state = "dead_letter"
            else:
                job.state = "retry"
                backoff = min(3600, 30 * (2 ** (job.attempts - 1)))
                if isinstance(exc, ProviderRateLimited):
                    backoff = max(backoff, exc.retry_after)
                job.next_run_at = naive_utc() + timedelta(seconds=backoff)
            audit("ingestion.failed", job_id=job_id, company_id=company_id,
                  provider=provider_name, state=job.state,
                  attempts=job.attempts, error_type=type(exc).__name__)
    return True
