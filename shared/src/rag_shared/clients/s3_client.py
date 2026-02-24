"""AWS S3 object storage client helper."""

from typing import Any, Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class S3Client:
    """Helper for AWS S3 object storage operations."""

    def __init__(
        self,
        region: str = "ap-south-1",
    ):
        """Initialize S3 client.

        Args:
            region: AWS region (credentials come from IAM role)
        """
        self.region = region
        self.client = boto3.client("s3", region_name=region)

    def health_check(self) -> bool:
        """Check S3 connection health.

        Returns:
            True if S3 is healthy
        """
        try:
            self.client.head_bucket(Bucket="ragqa-documents")
            return True
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            return False

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO | bytes,
        length: Optional[int] = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload object to bucket.

        Args:
            bucket_name: Target bucket
            object_name: Object path
            data: File-like object or bytes
            length: Data length (required for file-like objects)
            content_type: MIME type

        Returns:
            ETag of uploaded object
        """
        try:
            if isinstance(data, bytes):
                body = BytesIO(data)
            else:
                body = data

            response = self.client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=body,
                ContentType=content_type,
            )
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            return response.get("ETag", "").strip('"')
        except ClientError as e:
            logger.error(f"Failed to upload object: {e}")
            raise

    def get_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bytes:
        """Download object from bucket.

        Args:
            bucket_name: Source bucket
            object_name: Object path

        Returns:
            Object content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=bucket_name,
                Key=object_name,
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Failed to download object: {e}")
            raise

    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = False,
    ) -> list[str]:
        """List objects in bucket.

        Args:
            bucket_name: Target bucket
            prefix: Object prefix filter
            recursive: Include subdirectories (ignored in S3, always recursive)

        Returns:
            List of object names
        """
        try:
            objects = []
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        objects.append(obj["Key"])
            return objects
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            raise

    def remove_object(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        """Delete object from bucket.

        Args:
            bucket_name: Target bucket
            object_name: Object path
        """
        try:
            self.client.delete_object(
                Bucket=bucket_name,
                Key=object_name,
            )
            logger.info(f"Deleted {object_name} from {bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to delete object: {e}")
            raise

    def object_exists(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        """Check if object exists.

        Args:
            bucket_name: Target bucket
            object_name: Object path

        Returns:
            True if object exists
        """
        try:
            self.client.head_object(
                Bucket=bucket_name,
                Key=object_name,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def create_bucket(self, bucket_name: str) -> None:
        """Create new bucket if it doesn't exist.

        Args:
            bucket_name: Name for new bucket
        """
        try:
            try:
                self.client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    self.client.create_bucket(Bucket=bucket_name)
                    logger.info(f"Created bucket {bucket_name}")
                else:
                    raise
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    def list_buckets(self) -> list[str]:
        """Get list of all buckets.

        Returns:
            Bucket names
        """
        try:
            response = self.client.list_buckets()
            return [b["Name"] for b in response.get("Buckets", [])]
        except ClientError as e:
            logger.error(f"Failed to list buckets: {e}")
            raise

    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """Get presigned URL for object download.

        Args:
            bucket_name: Target bucket
            object_name: Object path
            expires: Expiry time in seconds

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_name},
                ExpiresIn=expires,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
