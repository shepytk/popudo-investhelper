from pathlib import Path

from scripts.check_compose_security import validate_compose


def test_private_infrastructure_and_required_credentials():
    project = Path(__file__).resolve().parents[3]
    assert validate_compose((project / "docker-compose.yml").read_text()) == []


def test_guard_catches_exposed_database():
    root = Path(__file__).resolve().parents[3]
    text = (root / "docker-compose.yml").read_text()
    altered = text.replace("    networks:\n      - backend", '    ports:\n      - "5432:5432"\n    networks:\n      - backend', 1)
    assert any("db publishes a port" in error for error in validate_compose(altered))
