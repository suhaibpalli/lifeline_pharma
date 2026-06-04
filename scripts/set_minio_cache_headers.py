"""
One-shot script: set Cache-Control on all existing MinIO objects.

Run once inside the Django container after deploying (optional if nginx A1 is done
since nginx already injects Cache-Control via add_header regardless of object metadata):

    docker exec -it pharma-django python scripts/set_minio_cache_headers.py

Requires MINIO_* env vars (already set in the container).
"""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharma_ecommerce.settings")
django.setup()

import boto3  # noqa: E402  (imported after django.setup())
from botocore.exceptions import ClientError  # noqa: E402
from django.conf import settings  # noqa: E402

CACHE_CONTROL = "public, max-age=31536000, immutable"


def run():
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    paginator = client.get_paginator("list_objects_v2")

    updated = 0
    skipped = 0
    errors = 0

    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            try:
                head = client.head_object(Bucket=bucket, Key=key)
                if head.get("CacheControl") == CACHE_CONTROL:
                    skipped += 1
                    continue

                # Copy-in-place to update metadata
                client.copy_object(
                    Bucket=bucket,
                    CopySource={"Bucket": bucket, "Key": key},
                    Key=key,
                    MetadataDirective="REPLACE",
                    CacheControl=CACHE_CONTROL,
                    ContentType=head.get("ContentType", "application/octet-stream"),
                )
                print(f"  ✓ {key}")
                updated += 1
            except ClientError as exc:
                print(f"  ✗ {key}: {exc}", file=sys.stderr)
                errors += 1

    print(f"\nDone. updated={updated} skipped={skipped} errors={errors}")


if __name__ == "__main__":
    run()
