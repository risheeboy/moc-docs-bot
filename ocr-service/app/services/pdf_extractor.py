"""PDF page extraction service."""

from typing import Optional, BinaryIO
from io import BytesIO
import structlog
from pdf2image import convert_from_bytes
from PIL import Image

logger = structlog.get_logger()


class PDFExtractor:
    """Extract pages from PDF as images."""

    def __init__(self):
        """Initialize PDF extractor."""
        pass

    def extract_pages(
        self,
        pdf_file: BinaryIO,
        dpi: int = 300,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
    ) -> list[dict]:
        """
        Extract pages from PDF file as images.

        Args:
            pdf_file: File-like object containing PDF data
            dpi: Resolution in DPI
            first_page: First page to extract (1-indexed, None = all)
            last_page: Last page to extract (1-indexed, None = all)

        Returns:
            List of dicts with 'image' (PIL Image) and 'page_number' keys
        """
        try:
            # Convert PDF to images
            logger.info("pdf_extraction_starting", dpi=dpi)

            images = convert_from_bytes(
                pdf_file.read(),
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                fmt="png",
            )

            pages_data = [
                {
                    "image": img,
                    "page_number": i + 1,
                }
                for i, img in enumerate(images)
            ]

            logger.info(
                "pdf_extraction_complete",
                num_pages=len(pages_data),
                dpi=dpi,
            )

            return pages_data

        except Exception as e:
            logger.error(
                "pdf_extraction_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError(f"Failed to extract PDF pages: {str(e)}")

    def extract_page_range(
        self,
        pdf_file: BinaryIO,
        start_page: int = 1,
        end_page: int = 10,
        dpi: int = 300,
    ) -> list[dict]:
        """
        Extract a specific range of pages from PDF.

        Args:
            pdf_file: File-like object containing PDF data
            start_page: First page to extract (1-indexed)
            end_page: Last page to extract (1-indexed)
            dpi: Resolution in DPI

        Returns:
            List of dicts with 'image' and 'page_number'
        """
        return self.extract_pages(pdf_file, dpi, start_page, end_page)

    def get_page_count(self, pdf_file: BinaryIO) -> int:
        """
        Get total page count without extracting images.

        Args:
            pdf_file: File-like object containing PDF data

        Returns:
            Number of pages
        """
        try:
            import PyPDF2

            pdf_reader = PyPDF2.PdfReader(pdf_file)
            return len(pdf_reader.pages)
        except ImportError:
            # Fallback: extract one page at high res and count
            try:
                images = convert_from_bytes(pdf_file.read(), dpi=72)
                return len(images)
            except Exception as e:
                logger.error("page_count_failed", error=str(e))
                return 0
