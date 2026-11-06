"""Archive and restore MinIO objects via its S3 API, without touching storage volumes.

Run inside the Compose API container with MINIO_ROOT_USER/PASSWORD injected.
Restores into NEW prefixed buckets only, and refuses existing destinations.
No request credentials are written to the archive or log output.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tarfile
from urllib.parse import quote, unquote

import boto3
from botocore.exceptions import ClientError

MAX_OBJECT_BYTES = 2 * 1024 * 1024 * 1024


def client():
    user = os.environ["MINIO_ROOT_USER"]
    password = os.environ["MINIO_ROOT_PASSWORD"]
    if not user or not password:
        raise ValueError("Missing object-store credentials")
    return boto3.client(
        "s3", endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
        aws_access_key_id=user, aws_secret_access_key=password,
        region_name="us-east-1",
    )


def backup(s3, output):
    with tarfile.open(fileobj=output, mode="w|") as archive:
        for bucket in sorted(b["Name"] for b in s3.list_buckets().get("Buckets", [])):
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for record in sorted(page.get("Contents", []), key=lambda obj: obj["Key"]):
                    key, size = record["Key"], record["Size"]
                    if size < 0 or size > MAX_OBJECT_BYTES:
                        raise ValueError("Refusing oversized object backup")
                    obj = s3.get_object(Bucket=bucket, Key=key)
                    try:
                        name = "objects/" + quote(bucket, safe="") + "/" + quote(key, safe="")
                        info = tarfile.TarInfo(name=name)
                        info.size = size
                        info.pax_headers = {"popudo.content_type": obj.get("ContentType", "application/octet-stream")}
                        archive.addfile(info, obj["Body"])
                    finally:
                        obj["Body"].close()


def restore(s3, stream, prefix: str):
    if not prefix or len(prefix) > 20 or not prefix.isascii() or not all(c.islower() or c.isdigit() or c == "-" for c in prefix):
        raise ValueError("Restore requires an alphanumeric lowercase destination prefix, e.g. recovered-")
    # Spool before starting to prevent partially restored objects when input is malformed.
    import tempfile
    with tempfile.TemporaryFile() as spool:
        while chunk := stream.read(1024 * 1024):
            spool.write(chunk)
        spool.seek(0)
        with tarfile.open(fileobj=spool, mode="r:") as archive:
            members = archive.getmembers()
            destinations = {}
            existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
            for member in members:
                parts = member.name.split("/")
                if not member.isfile() or len(parts) != 3 or parts[0] != "objects":
                    raise ValueError("Malformed object archive entry")
                bucket, key = unquote(parts[1]), unquote(parts[2])
                if quote(bucket, safe="") != parts[1] or quote(key, safe="") != parts[2]:
                    raise ValueError("Noncanonical archive entry")
                if not bucket or not key or member.size > MAX_OBJECT_BYTES or member.size < 0:
                    raise ValueError("Invalid object name or size")
                destination = prefix + bucket
                if len(destination) > 63 or destination in existing:
                    raise ValueError("Destination bucket already exists or has an invalid name")
                destinations[member.name] = (destination, key)
            for bucket in sorted(set(b for b, _ in destinations.values())):
                s3.create_bucket(Bucket=bucket)
            for member in members:
                bucket, key = destinations[member.name]
                body = archive.extractfile(member)
                if body is None:
                    raise ValueError("Missing archived object")
                s3.upload_fileobj(body, bucket, key, ExtraArgs={
                    "ContentType": member.pax_headers.get("popudo.content_type", "application/octet-stream")
                })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["backup", "restore"])
    parser.add_argument("--prefix", default="restored-")
    args = parser.parse_args()
    s3 = client()
    if args.command == "backup":
        backup(s3, sys.stdout.buffer)
    else:
        restore(s3, sys.stdin.buffer, args.prefix)


if __name__ == "__main__":
    main()
