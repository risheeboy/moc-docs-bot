import logging
from minio import Minio
from minio.error import S3Error
from typing import Optional, BinaryIO
from app.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """
    MinIO S3-compatible object storage client.

    Manages documents, processed text, images, and thumbnails.
    """

    def __init__(self):
        try:
            self.client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_use_ssl
            )

            # Ensure bucket exists
            self._ensure_bucket_exists(settings.minio_bucket_documents)
            logger.info(f"MinIO client initialized at {settings.minio_endpoint}")
        except Exception as e:
            logger.error(f"MinIO initialization error: {e}")
            self.client = None

    def _ensure_bucket_exists(self, bucket_name: str) -> bool:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Error ensuring bucket {bucket_name}: {e}")
            return False

    def upload_document(
        self,
        bucket: str,
        object_path: str,
        file_path: str
    ) -> bool:
        """
        Upload a document to MinIO.

        Args:
            bucket: Bucket name
            object_path: Path in bucket (e.g., "documents/raw/site/doc_id.pdf")
            file_path: Local file path

        Returns:
            True if successful
        """
        try:
            self._ensure_bucket_exists(bucket)
            self.client.fput_object(bucket, object_path, file_path)
            logger.info(f"Uploaded {object_path} to {bucket}")
            return True
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            return False

    def upload_bytes(
        self,
        bucket: str,
        object_path: str,
        data: bytes
    ) -> bool:
        """
        Upload raw bytes to MinIO.

        Args:
            bucket: Bucket name
            object_path: Path in bucket
            data: Bytes to upload

        Returns:
            True if successful
        """
        try:
            self._ensure_bucket_exists(bucket)
            self.client.put_object(
                bucket,
                object_path,
                io.BytesIO(data),
                len(data)
            )
            logger.info(f"Uploaded {len(data)} bytes to {object_path}")
            return True
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            return False

    def download_file(
        self,
        bucket: str,
        object_path: str,
        file_path: str
    ) -> bool:
        """
        Download a file from MinIO.

        Args:
            bucket: Bucket name
            object_path: Path in bucket
            file_path: Local file path to save

        Returns:
            True if successful
        """
        try:
            self.client.fget_object(bucket, object_path, file_path)
            logger.info(f"Downloaded {object_path} from {bucket}")
            return True
        except S3Error as e:
            logger.error(f"MinIO download error: {e}")
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
            from datetime import timedelta
            url = self.client.get_presigned_download_url(
                bucket,
                object_path,
                expires=timedelta(days=7)
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
            for obj in self.client.list_objects(bucket, prefix=prefix):
                objects.append(obj.object_name)
            return objects
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def delete_object(self, bucket: str, object_path: str) -> bool:
        """
        Delete an object from MinIO.

        Args:
            bucket: Bucket name
            object_path: Path in bucket

        Returns:
            True if successful
        """
        try:
            self.client.remove_object(bucket, object_path)
            logger.info(f"Deleted {object_path} from {bucket}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting object: {e}")
            return False


import io
