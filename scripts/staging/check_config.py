"""Staging deployment policy: no public ports and server-only API URL.

Usage: docker compose -f docker-compose.yml -f compose.staging.yaml config --format json |
       python3 scripts/staging/check_config.py
"""
from __future__ import annotations

import json
import sys


def validate(config: dict) -> list[str]:
    errors = []
    services = config.get("services", {})
    for name in ("db", "redis", "minio", "api", "web"):
        if name not in services:
            errors.append(f"Missing expected service: {name}")
    for name in ("db", "redis", "minio"):
        if services.get(name, {}).get("ports"):
            errors.append(f"Internal service {name} must not publish ports")
    for name in ("web", "api"):
        ports = services.get(name, {}).get("ports", [])
        if not ports:
            errors.append(f"Missing loopback port for {name}")
        for item in ports:
            ip = item.get("host_ip", "") if isinstance(item, dict) else ""
            if ip not in ("127.0.0.1", "::1"):
                errors.append(f"{name} must bind loopback only; got {ip!r}")
    web = services.get("web", {})
    wenv = web.get("environment", {})
    if isinstance(wenv, list):
        wenv = dict(s.split("=", 1) for s in wenv if "=" in s)
    if wenv.get("RESEARCH_API_INTERNAL_URL") != "http://api:8000":
        errors.append("Web server-side API must use Compose hostname http://api:8000")
    if wenv.get("NEXT_PUBLIC_API_BASE_URL"):
        errors.append("Never embed a public-facing API base in staging JavaScript")
    if wenv.get("NODE_ENV") != "production":
        errors.append("Next.js must run in production mode")
    api_env = services.get("api", {}).get("environment", {})
    if isinstance(api_env, list):
        api_env = dict(s.split("=", 1) for s in api_env if "=" in s)
    if api_env.get("INVESTHELPER_ENV") != "production":
        errors.append("API production-mode safeguards must be enabled")
    if api_env.get("INVESTHELPER_PUBLIC_DATA_PROVIDERS"):
        errors.append("Staging must not authorize provider redistribution")
    return errors


if __name__ == "__main__":
    errors = validate(json.load(sys.stdin))
    if errors:
        raise SystemExit("\n".join(errors))
    print("Private staging Compose configuration passes security contract")
