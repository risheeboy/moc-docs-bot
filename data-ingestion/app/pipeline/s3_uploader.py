"""S3 uploader for storing documents and media."""

import structlog
from typing import Optional
import uuid
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from app.config import settings
from app.utils.metrics import s3_upload_errors_total

logger = structlog.get_logger()


class S3Uploader:
    """Upload documents and media to AWS S3 object storage."""

    def __init__(self):
        """Initialize S3 client."""
        self.client = boto3.client("s3", region_name=settings.aws_default_region)
        self.bucket = settings.aws_s3_bucket_documents
        logger.info(
            "s3_client_initialized",
            region=settings.aws_default_region,
            bucket=self.bucket,
        )

    async def upload_raw_document(
        self,
        content: bytes,
        source_site: str,
        document_id: str,
        file_extension: str,
    ) -> Optional[str]:
        """Upload raw document to S3.

        Per §16: documents/raw/{source_site}/{document_id}.{ext}

        Args:
            content: Document content bytes
            source_site: Source site domain
            document_id: Document ID
            file_extension: File extension (html, pdf, docx, etc)

        Returns:
            S3 object path or None if upload fails
        """
        try:
            # Build object path per §16
            object_path = f"raw/{source_site}/{document_id}.{file_extension}"

            # Upload to S3
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_path,
                Body=BytesIO(content),
            )

            logger.info(
                "document_uploaded_to_s3",
                object_path=object_path,
                size_bytes=len(content),
            )

            return object_path

        except ClientError as e:
            logger.error(
                "s3_upload_error",
                document_id=document_id,
                error=str(e),
            )
            s3_upload_errors_total.inc()
            return None

    async def upload_processed_text(
        self,
        text: str,
        document_id: str,
    ) -> Optional[str]:
        """Upload processed text to S3.

        Per §16: documents/processed/{document_id}.txt

        Args:
            text: Processed text content
            document_id: Document ID

        Returns:
            S3 object path or None if upload fails
        """
        try:
            object_path = f"processed/{document_id}.txt"

            content = text.encode("utf-8")

            self.client.put_object(
                Bucket=self.bucket,
                Key=object_path,
                Body=BytesIO(content),
            )

            logger.debug(
                "processed_text_uploaded",
                object_path=object_path,
                size_bytes=len(content),
            )

            return object_path

        except ClientError as e:
            logger.error(
                "s3_text_upload_error",
                document_id=document_id,
                error=str(e),
            )
            s3_upload_errors_total.inc()
            return None

    async def upload_image(
        self,
        image_bytes: bytes,
        document_id: str,
        image_id: str = None,
    ) -> Optional[str]:
        """Upload image to S3.

        Per §16: documents/images/{document_id}/{image_id}.{ext}

        Args:
            image_bytes: Image content bytes
            document_id: Document ID
            image_id: Image ID (auto-generated if not provided)

        Returns:
            S3 object path or None if upload fails
        """
        try:
            if not image_id:
                image_id = str(uuid.uuid4())

            # Detect image format from header
            ext = self._detect_image_format(image_bytes)

            object_path = f"images/{document_id}/{image_id}.{ext}"

            self.client.put_object(
                Bucket=self.bucket,
                Key=object_path,
                Body=BytesIO(image_bytes),
            )

            logger.debug(
                "image_uploaded_to_s3",
                object_path=object_path,
                size_bytes=len(image_bytes),
            )

            return object_path

        except ClientError as e:
            logger.error(
                "s3_image_upload_error",
                document_id=document_id,
                error=str(e),
            )
            s3_upload_errors_total.inc()
            return None

    async def upload_thumbnail(
        self,
        image_bytes: bytes,
        document_id: str,
    ) -> Optional[str]:
        """Upload thumbnail to S3.

        Per §16: documents/thumbnails/{document_id}_thumb.jpg

        Args:
            image_bytes: Thumbnail bytes
            document_id: Document ID

        Returns:
            S3 object path or None if upload fails
        """
        try:
            object_path = f"thumbnails/{document_id}_thumb.jpg"

            self.client.put_object(
                Bucket=self.bucket,
                Key=object_path,
                Body=BytesIO(image_bytes),
            )

            logger.debug(
                "thumbnail_uploaded_to_s3",
                object_path=object_path,
            )

            return object_path

        except ClientError as e:
            logger.error(
                "s3_thumbnail_upload_error",
                document_id=document_id,
                error=str(e),
            )
            s3_upload_errors_total.inc()
            return None

    def get_object_url(self, object_path: str) -> str:
        """Get presigned URL for S3 object.

        Args:
            object_path: Object path in S3

        Returns:
            Presigned URL for accessing object (7 days)
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_path},
                ExpiresIn=7 * 24 * 60 * 60
            )
            return url
        except Exception as e:
            logger.error("Failed to generate presigned URL", error=str(e))
            return ""

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
