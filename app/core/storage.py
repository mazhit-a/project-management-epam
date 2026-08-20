"""Async S3 helpers for storing uploaded project documents.

Layout: bucket key = "{project_id}/{document_id}{ext}"
Keeping every project's files under its own key prefix lets project deletion
clean up storage with a single prefix-delete instead of enumerating rows.
"""

import contextlib
from typing import Any
from uuid import UUID

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings

_session = aioboto3.Session()


def _client(endpoint_url: str | None = None) -> Any:
    return _session.client(
        "s3",
        endpoint_url=endpoint_url or settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def project_prefix(project_id: UUID) -> str:
    return f"{project_id}/"


async def ensure_bucket() -> None:
    """Create the configured bucket if it doesn't exist yet.

    Only meant for local/dev emulators (MiniStack) that start empty on every
    restart. Real AWS buckets should be provisioned via IaC, not app code --
    callers must gate this on settings.is_production being False.
    """
    async with _client() as s3:
        with contextlib.suppress(ClientError):
            await s3.create_bucket(Bucket=settings.S3_BUCKET)


async def save_file(key: str, data: bytes, content_type: str, filename: str) -> None:
    async with _client() as s3:
        await s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
            ContentDisposition=f'attachment; filename="{filename}"',
        )


async def delete_file(key: str) -> None:
    async with _client() as s3:
        with contextlib.suppress(ClientError):
            await s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)


async def delete_prefix(prefix: str) -> None:
    async with _client() as s3:
        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=settings.S3_BUCKET, Prefix=prefix):
            objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if objects:
                await s3.delete_objects(Bucket=settings.S3_BUCKET, Delete={"Objects": objects})


async def presigned_download_url(key: str, expires_in: int = 300) -> str:
    async with _client(settings.s3_public_endpoint_url) as s3:
        url: str = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
