"""Redacted structured audit, low-cardinality metrics and correlation identifiers.

No secrets, user-supplied paths, request bodies, or provider payloads may be logged.
The metrics recorder is process-local (not a substitute for hosted aggregation).
"""
from __future__ import annotations

from collections import Counter
import json
import logging
import threading
import time
import uuid

from fastapi import Request

logger = logging.getLogger("investhelper.audit")

_ALLOWED_FIELDS = frozenset({
    "request_id", "route", "method", "status", "duration_ms",
    "provider", "company_id", "job_id", "attempts", "state",
    "snapshot_sha256", "facts_imported", "quotes_imported",
    "fx_imported", "listings_imported", "error_type",
    "count", "error_count", "latency_total_ms", "latency_max_ms",
    "status_class", "calculation_version", "calculation_run_id",
    "input_source", "outcome",
})


def audit(event: str, **fields) -> None:
    record = {"event": event, **{k: v for k, v in fields.items() if k in _ALLOWED_FIELDS and v is not None}}
    logger.info(json.dumps(record, default=str, separators=(",", ":"), sort_keys=True))


class HttpMetrics:
    """Bounded route/status-class counters suitable for a structured metrics sink."""

    def __init__(self, emit_every: int = 100):
        if emit_every < 1:
            raise ValueError("emit_every must be positive")
        self.emit_every = emit_every
        self._lock = threading.Lock()
        self._seen = 0
        self._data: dict[tuple[str, str, str], list[float]] = {}

    def observe(self, route: str, method: str, status: int, duration_ms: float) -> None:
        # Only known framework route templates are accepted, not raw URL paths.
        status_class = f"{status // 100}xx" if 100 <= status <= 599 else "unknown"
        route = route if route.startswith("/") and "?" not in route and len(route) < 120 else "<unmatched>"
        method = method if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
        key = (route, method, status_class)
        with self._lock:
            row = self._data.setdefault(key, [0.0, 0.0, 0.0])
            row[0] += 1
            row[1] += max(0.0, duration_ms)
            row[2] = max(row[2], duration_ms)
            self._seen += 1
            if self._seen < self.emit_every:
                return
            data = self._data
            self._data = {}
            self._seen = 0
        for (route_name, method_name, response_class), (count, total, maximum) in data.items():
            audit("http.metrics", route=route_name, method=method_name,
                  status_class=response_class, count=int(count),
                  error_count=int(count) if response_class.startswith("5") else 0,
                  latency_total_ms=round(total, 2), latency_max_ms=round(maximum, 2))


http_metrics = HttpMetrics()


def audit_calculation(*, run_id: str, version: str, source: str,
                      outcome: str, snapshot_hash: str | None = None) -> None:
    """Explicit hook for any server-run calculation. Never log numeric inputs."""
    audit("valuation.calculation", calculation_run_id=run_id,
          calculation_version=version, input_source=source,
          outcome=outcome, snapshot_sha256=snapshot_hash)


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
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        audit("http.request", request_id=request_id,
              route=route_name, method=request.method, status=status,
              duration_ms=duration_ms)
        http_metrics.observe(route_name, request.method, status, duration_ms)
