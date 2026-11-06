"""Fail-closed redistribution policy for sourced financial-data endpoints.

The allowlist is an operational *attestation* that an operator separately
confirmed licensing rights. This module cannot grant those rights itself.
Never infer redistribution permissions from the source being publicly reachable.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Iterable

from fastapi import HTTPException

from app.config import settings

_PROVIDER = re.compile(r"^[a-z][a-z0-9_-]{0,119}$")


@dataclass(frozen=True)
class PublicDataPolicy:
    production: bool
    approved_providers: frozenset[str]

    @classmethod
    def from_configuration(cls, environment: str, approval_csv: str) -> "PublicDataPolicy":
        if environment.strip().lower() != "production":
            return cls(False, frozenset())
        names = [value.strip().lower() for value in approval_csv.split(",") if value.strip()]
        if any(not _PROVIDER.fullmatch(name) for name in names):
            # A malformed allowlist must never accidentally turn off the gate.
            return cls(True, frozenset())
        return cls(True, frozenset(names))

    def is_permitted(self, provider: str | None) -> bool:
        if not self.production:
            return True
        return bool(provider) and bool(_PROVIDER.fullmatch(provider.lower())) and provider.lower() in self.approved_providers

    def require_all(self, providers: Iterable[str | None]) -> None:
        if not self.production:
            return
        if any(not self.is_permitted(p) for p in providers):
            raise HTTPException(
                status_code=403,
                detail={"code": "provider_license_restricted",
                        "message": "The selected source is not authorized for public redistribution."},
            )


def public_data_policy() -> PublicDataPolicy:
    return PublicDataPolicy.from_configuration(
        settings.env,
        os.getenv("INVESTHELPER_PUBLIC_DATA_PROVIDERS", ""),
    )


def enforce_public_data_providers(providers: Iterable[str | None]) -> None:
    public_data_policy().require_all(providers)
