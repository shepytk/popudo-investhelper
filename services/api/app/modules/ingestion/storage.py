"""Immutable content-addressed snapshot storage for local dev or S3-compatible MinIO."""
from __future__ import annotations

import hashlib
from pathlib import Path

from app.modules.ingestion.contracts import SnapshotStore


def object_key(provider: str, raw: bytes) -> tuple[str, str]:
    if not provider or not all(ch.isalnum() or ch in "_-" for ch in provider):
        raise ValueError("Unsafe provider identifier")
    digest = hashlib.sha256(raw).hexdigest()
    return f"{provider}/{digest[:2]}/{digest}", digest


class FileSnapshotStore(SnapshotStore):
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Unsafe snapshot path")
        return path

    def put_if_absent(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as handle:
                handle.write(data)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError("Immutable snapshot collision")

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()


class S3SnapshotStore(SnapshotStore):
    """boto3 S3/MinIO adapter; configured entirely by trusted deployment env."""

    def __init__(self, bucket: str, endpoint_url: str | None = None):
        import boto3

        self.bucket = bucket
        self.client = boto3.client("s3", endpoint_url=endpoint_url)

    def put_if_absent(self, key: str, data: bytes, content_type: str) -> None:
        # Conditional put avoids accidental overwrites under concurrent workers.
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                IfNoneMatch="*",
            )
        except self.client.exceptions.ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in {"PreconditionFailed", "412", "ConditionalRequestConflict", "409"}:
                raise
            if self.get(key) != data:
                raise ValueError("Immutable snapshot collision") from exc

    def get(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
