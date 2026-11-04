from pathlib import Path

from scripts.check_image_hygiene import check_image_hygiene


def test_base_images_are_versioned_and_infrastructure_private():
    root = Path(__file__).resolve().parents[3]
    files = {name: (root / name).read_text() for name in (
        "docker-compose.yml", "services/api/Dockerfile", "apps/web/Dockerfile",
    )}
    assert check_image_hygiene(files) == []


def test_detects_floating_tag_and_published_database():
    files = {
        "docker-compose.yml": 'services:\n  db:\n    image: postgres:latest\n    ports:\n      - "5432:5432"\n  api:\n    image: web:1\n',
    }
    errors = check_image_hygiene(files)
    assert any("unpinned" in x for x in errors)
    assert any("must not publish ports" in x for x in errors)
