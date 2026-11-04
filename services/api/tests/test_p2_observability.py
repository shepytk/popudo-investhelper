import json
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.observability import access_logs, audit


def test_audit_log_ignores_secrets_and_provider_raw_payload(caplog):
    with caplog.at_level(logging.INFO, logger="investhelper.audit"):
        audit(
            "ingestion.completed", company_id=7,
            provider="sec_edgar", snapshot_sha256="a" * 64,
            password="do-not-log", access_token="never-log",
            raw_payload="private-source-content",
        )
    payload = json.loads(caplog.records[-1].message)
    assert payload["provider"] == "sec_edgar"
    assert payload["snapshot_sha256"] == "a" * 64
    for forbidden in ("password", "access_token", "raw_payload", "do-not-log", "never-log"):
        assert forbidden not in caplog.records[-1].message


@pytest.mark.asyncio
async def test_request_logging_excludes_authorization_header_and_query(caplog):
    request = MagicMock()
    request.method = "GET"
    request.headers = {"Authorization": "Bearer secret-token"}
    request.url.query = "token=secret-query"
    request.scope = {"route": MagicMock(path="/api/companies/{company_id}")}
    response = MagicMock(status_code=200, headers={})

    async def next_response(req):
        return response

    with caplog.at_level(logging.INFO, logger="investhelper.audit"):
        result = await access_logs(request, next_response)
    assert result.headers["X-Request-ID"]
    log = caplog.records[-1].message
    assert "secret-token" not in log
    assert "secret-query" not in log
    assert "/api/companies/{company_id}" in log
