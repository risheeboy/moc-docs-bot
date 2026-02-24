"""MinIO uploader for storing documents and media."""

import structlog
from typing import Optional, BinaryIO
import uuid
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.config import settings
from app.utils.metrics import minio_upload_errors_total

logger = structlog.get_logger()


class MinIOUploader:
    """Upload documents and media to MinIO object storage."""

    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        self.bucket = settings.minio_bucket_documents

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure MinIO bucket exists, create if needed."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(
                    "minio_bucket_created",
                    bucket=self.bucket,
                )
            else:
                logger.debug(
                    "minio_bucket_exists",
                    bucket=self.bucket,
                )

        except S3Error as e:
            logger.error(
                "minio_bucket_error",
                bucket=self.bucket,
                error=str(e),
            )

    async def upload_raw_document(
        self,
        content: bytes,
        source_site: str,
        document_id: str,
        file_extension: str,
    ) -> Optional[str]:
        """Upload raw document to MinIO.

        Per §16: documents/raw/{source_site}/{document_id}.{ext}

        Args:
            content: Document content bytes
            source_site: Source site domain
            document_id: Document ID
            file_extension: File extension (html, pdf, docx, etc)

        Returns:
            MinIO object path or None if upload fails
        """
        try:
            # Build object path per §16
            object_path = f"raw/{source_site}/{document_id}.{file_extension}"

            # Upload to MinIO
            self.client.put_object(
                self.bucket,
                object_path,
                BytesIO(content),
                len(content),
            )

            logger.info(
                "document_uploaded_to_minio",
                object_path=object_path,
                size_bytes=len(content),
            )

            return object_path

        except S3Error as e:
            logger.error(
                "minio_upload_error",
                document_id=document_id,
                error=str(e),
            )
            minio_upload_errors_total.inc()
            return None

    async def upload_processed_text(
        self,
        text: str,
        document_id: str,
    ) -> Optional[str]:
        """Upload processed text to MinIO.

        Per §16: documents/processed/{document_id}.txt

        Args:
            text: Processed text content
            document_id: Document ID

        Returns:
            MinIO object path or None if upload fails
        """
        try:
            object_path = f"processed/{document_id}.txt"

            content = text.encode("utf-8")

            self.client.put_object(
                self.bucket,
                object_path,
                BytesIO(content),
                len(content),
            )

            logger.debug(
                "processed_text_uploaded",
                object_path=object_path,
                size_bytes=len(content),
            )

            return object_path

        except S3Error as e:
            logger.error(
                "minio_text_upload_error",
                document_id=document_id,
                error=str(e),
            )
            minio_upload_errors_total.inc()
            return None

    async def upload_image(
        self,
        image_bytes: bytes,
        document_id: str,
        image_id: str = None,
    ) -> Optional[str]:
        """Upload image to MinIO.

        Per §16: documents/images/{document_id}/{image_id}.{ext}

        Args:
            image_bytes: Image content bytes
            document_id: Document ID
            image_id: Image ID (auto-generated if not provided)

        Returns:
            MinIO object path or None if upload fails
        """
        try:
            if not image_id:
                image_id = str(uuid.uuid4())

            # Detect image format from header
            ext = self._detect_image_format(image_bytes)

            object_path = f"images/{document_id}/{image_id}.{ext}"

            self.client.put_object(
                self.bucket,
                object_path,
                BytesIO(image_bytes),
                len(image_bytes),
            )

            logger.debug(
                "image_uploaded_to_minio",
                object_path=object_path,
                size_bytes=len(image_bytes),
            )

            return object_path

        except S3Error as e:
            logger.error(
                "minio_image_upload_error",
                document_id=document_id,
                error=str(e),
            )
            minio_upload_errors_total.inc()
            return None

    async def upload_thumbnail(
        self,
        image_bytes: bytes,
        document_id: str,
    ) -> Optional[str]:
        """Upload thumbnail to MinIO.

        Per §16: documents/thumbnails/{document_id}_thumb.jpg

        Args:
            image_bytes: Thumbnail bytes
            document_id: Document ID

        Returns:
            MinIO object path or None if upload fails
        """
        try:
            object_path = f"thumbnails/{document_id}_thumb.jpg"

            self.client.put_object(
                self.bucket,
                object_path,
                BytesIO(image_bytes),
                len(image_bytes),
            )

            logger.debug(
                "thumbnail_uploaded_to_minio",
                object_path=object_path,
            )

            return object_path

        except S3Error as e:
            logger.error(
                "minio_thumbnail_upload_error",
                document_id=document_id,
                error=str(e),
            )
            minio_upload_errors_total.inc()
            return None

    def get_object_url(self, object_path: str) -> str:
        """Get public URL for MinIO object.

        Args:
            object_path: Object path in MinIO

        Returns:
            HTTP URL for accessing object
        """
        protocol = "https" if settings.minio_use_ssl else "http"
        return f"{protocol}://{settings.minio_endpoint}/{self.bucket}/{object_path}"

    @staticmethod
    def _detect_image_format(image_bytes: bytes) -> str:
        """Detect image format from file header.

        Args:
            image_bytes: Image bytes

        Returns:
            File extension (jpg, png, gif, webp, etc)
        """
        if image_bytes[:3] == b"\xff\xd8\xff":
            return "jpg"
        elif image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        elif image_bytes[:6] == b"GIF87a" or image_bytes[:6] == b"GIF89a":
            return "gif"
        elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "webp"
        elif image_bytes[:4] == b"\x00\x00\x01\x00":
            return "ico"
        else:
            return "jpg"  # Default to jpg
