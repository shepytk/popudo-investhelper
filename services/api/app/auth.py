"""OIDC resource-server authentication. No development bypass in deployed routes."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError


@dataclass(frozen=True)
class Principal:
    user_id: str


bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=8)
def _jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=300)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> Principal:
    issuer = os.getenv("INVESTHELPER_OIDC_ISSUER", "").rstrip("/")
    audience = os.getenv("INVESTHELPER_OIDC_AUDIENCE", "")
    jwks_url = os.getenv("INVESTHELPER_OIDC_JWKS_URL", "")
    url = urlsplit(jwks_url)
    if not issuer.startswith("https://") or not audience or url.scheme != "https" or not url.hostname or url.username:
        raise HTTPException(status_code=503, detail={"code": "auth_not_configured", "message": "Authentication is unavailable"})
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"code": "not_authenticated", "message": "Bearer token required"}, headers={"WWW-Authenticate": "Bearer"})
    try:
        key = _jwk_client(jwks_url).get_signing_key_from_jwt(credentials.credentials)
        payload = jwt.decode(
            credentials.credentials, key.key,
            algorithms=["RS256"], issuer=issuer, audience=audience,
            options={"require": ["sub", "exp", "iat", "iss", "aud"]},
            leeway=30,
        )
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub.strip() or len(sub) > 120:
            raise ValueError("Invalid subject")
    except (PyJWTError, ValueError, KeyError, TypeError, OSError):
        raise HTTPException(status_code=401, detail={"code": "invalid_token", "message": "Invalid or expired access token"}, headers={"WWW-Authenticate": "Bearer"})
    return Principal(user_id=sub)
