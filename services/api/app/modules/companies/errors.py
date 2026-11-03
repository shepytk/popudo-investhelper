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


def domain_error(status_code: int, code: ErrorCode, message: str, *, retryable: bool = False):
    """Consistent machine-readable domain error; separate from validation 422s."""
    from fastapi import HTTPException

    payload = ErrorDetail(code=code, message=message, retryable=retryable)
    return HTTPException(status_code=status_code, detail=payload.model_dump())
