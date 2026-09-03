# ─────────────────────────────────────────────────────────────
# uploader.py  —  AWS S3 upload helpers
# ─────────────────────────────────────────────────────────────

import boto3
import logging
import os
from datetime import datetime, timezone
from botocore.exceptions import BotoCoreError, ClientError
from config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    S3_BUCKET, S3_PREFIX, KEEP_LOCAL_COPY,
)

logger = logging.getLogger(__name__)

# Lazy singleton S3 client
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        logger.info(f"S3 client initialised — region: {AWS_REGION}, bucket: {S3_BUCKET}")
    return _s3_client


def _build_s3_key(camera_name: str, filename: str) -> str:
    """
    Build an organised S3 key:
      <prefix>/<camera_name>/YYYY-MM-DD/<filename>
    """
    date_folder = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    return f"{S3_PREFIX}/{camera_name}/{date_folder}/{filename}"


def upload_bytes(data: bytes, camera_name: str, filename: str) -> bool:
    """
    Upload raw bytes (e.g. a JPEG frame) directly to S3.
    """
    s3_key    = _build_s3_key(camera_name, filename)
    content_type = "image/jpeg" if filename.endswith(".jpg") else "application/octet-stream"

    try:
        get_s3_client().put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=data,
            ContentType=content_type,
        )
        logger.info(f"[{camera_name}] Uploaded → s3://{S3_BUCKET}/{s3_key}")
        return True
    except (BotoCoreError, ClientError) as e:
        logger.error(f"[{camera_name}] S3 upload failed: {e}")
        return False


def upload_file(local_path: str, camera_name: str, filename: str) -> bool:
    """
    Upload a local file (e.g. an MP4 clip) to S3.
    Optionally deletes the local file after a successful upload.
    """
    if not os.path.exists(local_path):
        logger.error(f"[{camera_name}] File not found: {local_path}")
        return False

    s3_key       = _build_s3_key(camera_name, filename)
    content_type = "video/mp4" if filename.endswith(".mp4") else "application/octet-stream"

    try:
        get_s3_client().upload_file(
            local_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info(f"[{camera_name}] Uploaded → s3://{S3_BUCKET}/{s3_key}")

        if not KEEP_LOCAL_COPY:
            os.remove(local_path)
            logger.debug(f"[{camera_name}] Deleted local file: {local_path}")

        return True
    except (BotoCoreError, ClientError) as e:
        logger.error(f"[{camera_name}] S3 upload failed: {e}")
        return False


def verify_bucket_access() -> bool:
    """
    Quick connectivity check — verify the bucket exists and is accessible.
    Call this once at startup before running the pipeline.
    """
    try:
        get_s3_client().head_bucket(Bucket=S3_BUCKET)
        logger.info(f"Bucket access verified: s3://{S3_BUCKET}")
        return True
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "403":
            logger.error(f"Access denied to bucket: {S3_BUCKET}")
        elif code == "404":
            logger.error(f"Bucket not found: {S3_BUCKET}")
        else:
            logger.error(f"Bucket check failed: {e}")
        return False
