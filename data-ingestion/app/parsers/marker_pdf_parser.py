"""PDF parsing using Marker for high-quality text extraction."""

import structlog
from typing import Optional
from io import BytesIO

logger = structlog.get_logger()


class MarkerPdfParser:
    """Parser for extracting text from PDFs using Marker."""

    def __init__(self):
        """Initialize PDF parser."""
        # Marker will be imported on demand to avoid startup issues
        self._marker = None

    async def parse_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Parse PDF from bytes.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Extracted text or None if parsing fails
        """
        try:
            # Try Marker first (high-quality PDFs)
            text = await self._parse_with_marker(pdf_bytes)

            if text and len(text.strip()) > 0:
                return text

            # Fallback to PyMuPDF
            text = await self._parse_with_pymupdf(pdf_bytes)
            return text

        except Exception as e:
            logger.warning(
                "pdf_parsing_error",
                error=str(e),
            )
            return None

    async def _parse_with_marker(self, pdf_bytes: bytes) -> Optional[str]:
        """Parse PDF using Marker.

        Args:
            pdf_bytes: PDF file content

        Returns:
            Extracted text or None
        """
        try:
            from marker.pdf_model import PDFModel
            from marker.pdf_extract import extract_text_from_pdf
            import tempfile
            import os

            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as temp_file:
                temp_file.write(pdf_bytes)
                temp_path = temp_file.name

            try:
                # Extract text using Marker
                text = extract_text_from_pdf(temp_path)
                return text

            finally:
                os.unlink(temp_path)

        except Exception as e:
            logger.debug(
                "marker_pdf_parsing_failed",
                error=str(e),
            )
            return None

    async def _parse_with_pymupdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Parse PDF using PyMuPDF (fallback).

        Args:
            pdf_bytes: PDF file content

        Returns:
            Extracted text or None
        """
        try:
            import fitz  # PyMuPDF

            pdf_stream = BytesIO(pdf_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            text_parts = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()

            return "\n".join(text_parts) if text_parts else None

        except Exception as e:
            logger.warning(
                "pymupdf_parsing_error",
                error=str(e),
            )
            return None

    async def extract_metadata(self, pdf_bytes: bytes) -> dict:
        """Extract metadata from PDF.

        Args:
            pdf_bytes: PDF file content

        Returns:
            Dictionary with PDF metadata
        """
        try:
            import fitz  # PyMuPDF

            pdf_stream = BytesIO(pdf_bytes)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")

            metadata = {
                "pages": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
            }

            doc.close()

            return metadata

        except Exception as e:
            logger.warning(
                "pdf_metadata_extraction_error",
                error=str(e),
            )
            return {}
