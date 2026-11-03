"""Real S3-compatible MinIO integration, opt-in through CI service."""
import os

import pytest

from app.modules.ingestion.storage import S3SnapshotStore, object_key


@pytest.mark.skipif(not os.getenv("P1_MINIO_ENDPOINT"), reason="MinIO integration environment not configured")
def test_minio_snapshots_are_immutable_and_hash_addressed():
    import boto3

    endpoint = os.environ["P1_MINIO_ENDPOINT"]
    bucket = "p1-source-verification"
    client = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
    try:
        client.create_bucket(Bucket=bucket)
    except client.exceptions.BucketAlreadyOwnedByYou:
        pass
    store = S3SnapshotStore(bucket, endpoint)
    key, digest = object_key("sec_edgar", b"SEC example source")
    store.put_if_absent(key, b"SEC example source", "application/json")
    store.put_if_absent(key, b"SEC example source", "application/json")
    assert store.get(key) == b"SEC example source"
    assert key.endswith(digest)
    with pytest.raises(ValueError, match="Immutable snapshot collision"):
        store.put_if_absent(key, b"altered unverified source", "application/json")
