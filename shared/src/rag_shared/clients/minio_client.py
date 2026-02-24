"""MinIO object storage client helper."""

from typing import Any, Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    """Helper for MinIO object storage operations."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        use_ssl: bool = False,
    ):
        """Initialize MinIO client.

        Args:
            endpoint: MinIO server endpoint (host:port)
            access_key: Access key
            secret_key: Secret key
            use_ssl: Use HTTPS (default False for internal network)
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.use_ssl = use_ssl
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=use_ssl,
        )

    def health_check(self) -> bool:
        """Check MinIO connection health.

        Returns:
            True if MinIO is healthy
        """
        try:
            # Try to list buckets
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
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
                result = self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=data,  # type: ignore
                    length=len(data),
                    content_type=content_type,
                )
            else:
                result = self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=data,
                    length=length or -1,
                    content_type=content_type,
                )
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            return result.etag
        except S3Error as e:
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
                bucket_name=bucket_name,
                object_name=object_name,
            )
            return response.read()
        except S3Error as e:
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
            recursive: Include subdirectories

        Returns:
            List of object names
        """
        try:
            objects = []
            for obj in self.client.list_objects(
                bucket_name=bucket_name,
                prefix=prefix,
                recursive=recursive,
            ):
                objects.append(obj.object_name)
            return objects
        except S3Error as e:
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
            self.client.remove_object(
                bucket_name=bucket_name,
                object_name=object_name,
            )
            logger.info(f"Deleted {object_name} from {bucket_name}")
        except S3Error as e:
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
            self.client.stat_object(
                bucket_name=bucket_name,
                object_name=object_name,
            )
            return True
        except S3Error:
            return False

    def create_bucket(self, bucket_name: str) -> None:
        """Create new bucket if it doesn't exist.

        Args:
            bucket_name: Name for new bucket
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket {bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    def list_buckets(self) -> list[str]:
        """Get list of all buckets.

        Returns:
            Bucket names
        """
        try:
            buckets = self.client.list_buckets()
            return [b.name for b in buckets]
        except S3Error as e:
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
            url = self.client.get_presigned_download_url(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
