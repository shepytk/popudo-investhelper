from typing import Literal

from pydantic import BaseModel


ErrorCode = Literal[
    "company_not_found",
    "listing_not_found",
    "unsupported_industry",
    "missing_filing",
    "missing_data",
    "stale_data",
    "invalid_as_of",
    "not_computable",
    "provider_unavailable",
    "invalid_provenance",
]


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    retryable: bool = False


class ErrorResponse(BaseModel):
    detail: ErrorDetail
