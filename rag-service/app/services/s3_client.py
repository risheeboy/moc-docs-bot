import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from app.config import settings
from io import BytesIO

logger = logging.getLogger(__name__)


class S3Client:
    """
    AWS S3 object storage client.

    Manages documents, processed text, images, and thumbnails.
    """

    def __init__(self):
        try:
            self.client = boto3.client("s3", region_name=settings.aws_default_region)
            self.bucket_documents = settings.aws_s3_bucket_documents
            logger.info(f"S3 client initialized in region {settings.aws_default_region}")
        except Exception as e:
            logger.error(f"S3 initialization error: {e}")
            self.client = None

    def upload_document(
        self,
        bucket: str,
        object_path: str,
        file_path: str
    ) -> bool:
        """
        Upload a document to S3.

        Args:
            bucket: Bucket name
            object_path: Path in bucket (e.g., "documents/raw/site/doc_id.pdf")
            file_path: Local file path

        Returns:
            True if successful
        """
        try:
            with open(file_path, "rb") as f:
                self.client.upload_fileobj(f, bucket, object_path)
            logger.info(f"Uploaded {object_path} to {bucket}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return False

    def upload_bytes(
        self,
        bucket: str,
        object_path: str,
        data: bytes
    ) -> bool:
        """
        Upload raw bytes to S3.

        Args:
            bucket: Bucket name
            object_path: Path in bucket
            data: Bytes to upload

        Returns:
            True if successful
        """
        try:
            self.client.put_object(
                Bucket=bucket,
                Key=object_path,
                Body=BytesIO(data)
            )
            logger.info(f"Uploaded {len(data)} bytes to {object_path}")
            return True
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return False

    def download_file(
        self,
        bucket: str,
        object_path: str,
        file_path: str
    ) -> bool:
        """
        Download a file from S3.

        Args:
            bucket: Bucket name
            object_path: Path in bucket
            file_path: Local file path to save

        Returns:
            True if successful
        """
        try:
            self.client.download_file(bucket, object_path, file_path)
            logger.info(f"Downloaded {object_path} from {bucket}")
            return True
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            return False

    def get_object_url(self, bucket: str, object_path: str) -> Optional[str]:
        """
        Get presigned URL for an object (valid for 7 days).

        Args:
            bucket: Bucket name
            object_path: Path in bucket

        Returns:
            Presigned URL or None if error
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_path},
                ExpiresIn=7 * 24 * 60 * 60
            )
            return url
        except Exception as e:
            logger.error(f"Error getting presigned URL: {e}")
            return None

    def list_objects(
        self,
        bucket: str,
        prefix: str = ""
    ) -> list:
        """
        List objects in bucket with optional prefix.

        Args:
            bucket: Bucket name
            prefix: Prefix to filter objects

        Returns:
            List of object names
        """
        try:
            objects = []
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        objects.append(obj["Key"])
            return objects
        except ClientError as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def delete_object(self, bucket: str, object_path: str) -> bool:
        """
        Delete an object from S3.

        Args:
            bucket: Bucket name
            object_path: Path in bucket

        Returns:
            True if successful
        """
        try:
            self.client.delete_object(Bucket=bucket, Key=object_path)
            logger.info(f"Deleted {object_path} from {bucket}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object: {e}")
            return False
