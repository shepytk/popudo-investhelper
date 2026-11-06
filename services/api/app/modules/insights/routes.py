from datetime import datetime, timezone
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, FinancialStatement, Insight
from app.licensing import public_data_policy
from app.modules.companies.verification import verified_statements
from app.modules.companies.errors import domain_error
from app.modules.insights.schemas import AIInsightOut
from app.modules.insights.service import DISCLAIMER, generate_verified_insight
from app.shared.database.session import get_db

router = APIRouter(prefix="/api/ai/companies", tags=["research-insights"])


@router.post("/{company_id}/generate-insight", response_model=AIInsightOut)
def generate_insight(company_id: int, db: Session = Depends(get_db)):
    if public_data_policy().production:
        raise domain_error(403, "provider_license_restricted",
                           "Derived insights cannot be published until their source licences are attested.")
    company = db.get(Company, company_id)
    if not company:
        raise domain_error(404, "company_not_found", "Company not found")

    statements = list(db.scalars(
        select(FinancialStatement)
        .where(FinancialStatement.company_id == company_id)
        .where(FinancialStatement.period_type == "annual")
        .order_by(FinancialStatement.period_end_date.desc())
    ))
    verified = verified_statements(statements)
    if not verified:
        raise domain_error(422, "not_computable", "No current annual financial statement with validated source, currency, units and reconciled cash flow.")
    payload, snapshot = generate_verified_insight(company, verified[0])
    db.add(Insight(
        company_id=company_id,
        date=datetime.now(timezone.utc).date(),
        quality_score=None,
        growth_score=None,
        valuation_score=None,
        balance_sheet_score=None,
        risk_score=None,
        overall_score=None,
        summary=payload["summary"],
        thesis=payload["quality_view"],
        risks=json.dumps(payload["risks"]),
        opportunities=json.dumps(payload["opportunities"]),
        questions_for_further_research=json.dumps(payload["questions_for_further_research"]),
        analysis_status="partial_verified",
        evidence_json=json.dumps({
            "as_of": payload["as_of"],
            "evidence": payload["evidence"],
            "business_model": payload["business_model"],
            "growth_view": payload["growth_view"],
            "valuation_view": payload["valuation_view"],
            "balance_sheet_view": payload["balance_sheet_view"],
            "risk_view": payload["risk_view"],
        }),
        source_snapshot_id=snapshot,
    ))
    db.commit()
    return payload


@router.get("/{company_id}/insights", response_model=list[AIInsightOut])
def list_insights(
    company_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if public_data_policy().production:
        raise domain_error(403, "provider_license_restricted",
                           "Derived insights cannot be published until their source licences are attested.")
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Legacy rows have fixed, fabricated scores and no evidence. Never serve them.
    items = list(db.scalars(
        select(Insight)
        .where(Insight.company_id == company_id)
        .where(Insight.analysis_status == "partial_verified")
        .where(Insight.evidence_json.is_not(None))
        .order_by(Insight.created_at.desc())
        .limit(limit)
        .offset(offset)
    ))
    output = []
    for item in items:
        stored = json.loads(item.evidence_json)
        output.append({
            "status": "partial_verified",
            "as_of": stored["as_of"],
            "evidence": stored["evidence"],
            "summary": item.summary,
            "business_model": stored["business_model"],
            "quality_view": item.thesis,
            "growth_view": stored["growth_view"],
            "valuation_view": stored["valuation_view"],
            "balance_sheet_view": stored["balance_sheet_view"],
            "risk_view": stored["risk_view"],
            "opportunities": json.loads(item.opportunities),
            "risks": json.loads(item.risks),
            "questions_for_further_research": json.loads(item.questions_for_further_research),
            "disclaimer": DISCLAIMER,
        })
    return output
