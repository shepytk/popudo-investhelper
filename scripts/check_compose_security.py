"""Static Compose security guard (no Docker required)."""
from pathlib import Path
import re

COMPOSE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


def validate_compose(text: str) -> list[str]:
    errors = []
    # All named infra services must stay on the private Compose network.
    for name in ("db", "redis", "minio"):
        marker = f"  {name}:"
        if marker not in text:
            errors.append(f"Missing infrastructure service {name}")
            continue
        after = text.split(marker, 1)[1]
        boundary = re.search(r"(?m)^  [a-z][a-z0-9_-]*:[ ]*$", after)
        until = boundary.start() if boundary else -1
        block = after if until == -1 else after[:until]
        if "\n    ports:" in block:
            errors.append(f"Infrastructure service {name} publishes a port")
        if "backend" not in block:
            errors.append(f"Infrastructure service {name} is not on backend network")
    for key in ("POSTGRES_PASSWORD:?", "MINIO_ROOT_PASSWORD:?"):
        if key not in text:
            errors.append(f"Missing mandatory secret interpolation: {key}")
    return errors


if __name__ == "__main__":
    errors = validate_compose(COMPOSE.read_text())
    if errors:
        raise SystemExit("\n".join(errors))
    print("Compose infrastructure isolation and mandatory secrets verified")
