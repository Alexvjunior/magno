"""S3 helpers — store generated XLSX exports and produce presigned URLs."""
from __future__ import annotations

import os

import boto3

BUCKET = os.environ.get("EXPORTS_BUCKET", "")
_s3 = boto3.client("s3")


def upload_xlsx(key: str, data: bytes) -> None:
    if not BUCKET:
        raise RuntimeError("EXPORTS_BUCKET env var not set")
    _s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=data,
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def presigned_get(key: str, expires_seconds: int = 900) -> str:
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires_seconds,
    )
