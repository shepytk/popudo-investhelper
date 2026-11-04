"""Structured JSON logs with low-cardinality labels and no credentials.

Never include request headers, query strings, Authorization, cookies, or full
provider responses. IDs are generated server-side for trustworthiness.
"""
from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("investhelper.audit")


def audit(event: str, **fields) -> None:
    allowed = {
        "request_id", "route", "method", "status", "duration_ms",
        "provider", "company_id", "job_id", "attempts", "state",
        "snapshot_sha256", "facts_imported", "quotes_imported",
        "fx_imported", "listings_imported", "error_type",
    }
    record = {"event": event, **{k: v for k, v in fields.items() if k in allowed and v is not None}}
    logger.info(json.dumps(record, default=str, separators=(",", ":"), sort_keys=True))


async def access_logs(request: Request, call_next):
    request_id = uuid.uuid4().hex
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        route = request.scope.get("route")
        route_name = getattr(route, "path", "<unmatched>")
        audit(
            "http.request", request_id=request_id,
            route=route_name, method=request.method, status=status,
            duration_ms=round((time.perf_counter() - start) * 1000, 2),
        )
