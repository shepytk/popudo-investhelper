"""Fail CI when the base local stack uses floating or insecure images."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [ROOT / "docker-compose.yml", ROOT / "apps/web/Dockerfile", ROOT / "services/api/Dockerfile"]


def check_image_hygiene(files: dict[str, str]) -> list[str]:
    findings: list[str] = []
    for name, body in files.items():
        for line in body.splitlines():
            text = line.strip()
            match = re.match(r"(?:image:|FROM)\s+([^\s#]+)", text, flags=re.IGNORECASE)
            if not match:
                continue
            reference = match.group(1)
            if reference.endswith(":latest") or (":" not in reference.split("/")[-1] and "@sha256:" not in reference):
                findings.append(f"{name}: unpinned container reference {reference}")
            if reference.startswith("http://"):
                findings.append(f"{name}: insecure container reference")
        if name.endswith("docker-compose.yml"):
            for service in ("db", "redis", "minio"):
                section = re.search(rf"(?ms)^  {service}:\n(.*?)(?=^  [a-z][a-z0-9_-]*:|^networks:|\Z)", body)
                if section and re.search(r"(?m)^    ports:", section.group(1)):
                    findings.append(f"{name}: {service} must not publish ports")
    return findings


if __name__ == "__main__":
    data = {str(f.relative_to(ROOT)): f.read_text(encoding="utf8") for f in CHECKS}
    errors = check_image_hygiene(data)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Image tags and infrastructure port configuration pass static policy")
