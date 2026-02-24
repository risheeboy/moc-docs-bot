"""EasyOCR Engine for Hindi and English (fallback for degraded text)."""

from typing import Optional, Any
import easyocr
from PIL import Image
import structlog
import re

from app.config import settings
from app.services.preprocessor import ImagePreprocessor
from app.services.postprocessor import PostProcessor

logger = structlog.get_logger()


class EasyOCREngine:
    """EasyOCR-based OCR engine for degraded/handwritten text."""

    def __init__(self):
        """Initialize EasyOCR engine."""
        self.reader = None
        self.preprocessor = ImagePreprocessor(
            enable_deskew=settings.deskew_enabled,
            enable_denoise=settings.denoise_enabled,
            enable_binarize=settings.binarize_enabled,
        )
        self.postprocessor = PostProcessor()

    def _get_reader(self, languages: str):
        """
        Lazily initialize EasyOCR reader.

        Args:
            languages: Language codes (e.g., "hi,en")
        """
        lang_list = self._normalize_languages(languages)

        if self.reader is None:
            logger.info("easyocr_initializing", languages=lang_list)
            self.reader = easyocr.Reader(
                lang_list,
                gpu=False,  # CPU mode for stability
                model_storage_directory=settings.model_cache_dir,
            )

        return self.reader

    def process(
        self,
        image: Image.Image,
        languages: str,
        page_number: int = 1,
    ) -> dict[str, Any]:
        """
        Process image with EasyOCR.

        Args:
            image: PIL Image
            languages: Language codes (e.g., "hi,en")
            page_number: Page number for reference

        Returns:
            Dict with text, regions, confidence, etc.
        """
        try:
            # Preprocess image
            if settings.enable_preprocessing:
                processed_image = self.preprocessor.preprocess(image)
            else:
                processed_image = image

            reader = self._get_reader(languages)

            logger.info(
                "easyocr_processing",
                languages=languages,
                page_number=page_number,
            )

            # Run OCR
            results = reader.readtext(
                processed_image,
                detail=1,  # Include confidence and bounding boxes
            )

            # Extract regions and text
            regions = []
            text_parts = []
            confidences = []

            for (bbox, text, confidence) in results:
                if not text.strip():
                    continue

                # Convert bbox format [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] to [x1, y1, x2, y2]
                xs = [point[0] for point in bbox]
                ys = [point[1] for point in bbox]
                x1, x2 = int(min(xs)), int(max(xs))
                y1, y2 = int(min(ys)), int(max(ys))

                regions.append(
                    {
                        "text": text,
                        "bounding_box": [x1, y1, x2, y2],
                        "confidence": float(confidence),
                        "type": "paragraph",
                    }
                )

                text_parts.append(text)
                confidences.append(confidence)

            # Combine text
            full_text = "\n".join(text_parts)

            # Post-process text
            full_text = self.postprocessor.postprocess(full_text, languages)

            # Calculate overall confidence
            overall_confidence = (
                sum(confidences) / len(confidences)
                if confidences
                else 0.5
            )

            result = {
                "page_number": page_number,
                "text": full_text,
                "regions": regions,
                "confidence": min(overall_confidence, 1.0),
                "language": self._detect_language(full_text),
                "engine": "easyocr",
            }

            logger.info(
                "easyocr_processing_complete",
                page_number=page_number,
                num_regions=len(regions),
                confidence=result["confidence"],
            )

            return result

        except Exception as e:
            logger.error(
                "easyocr_processing_error",
                error=str(e),
                page_number=page_number,
            )
            raise

    def _normalize_languages(self, languages: str) -> list[str]:
        """
        Normalize language codes for EasyOCR.

        EasyOCR uses ISO codes like "en", "hi", etc.

        Args:
            languages: Language codes (e.g., "hi,en" or "hin+eng")

        Returns:
            List for EasyOCR (e.g., ["hi", "en"])
        """
        mapping = {
            "hin": "hi",
            "eng": "en",
            "ben": "bn",
            "tel": "te",
            "mar": "mr",
            "tam": "ta",
            "urd": "ur",
            "guj": "gu",
            "kan": "kn",
            "mal": "ml",
            "ory": "or",
            "pan": "pa",
        }

        # Split by comma or plus
        codes = re.split(r"[,+]", languages.strip())
        normalized = []

        for code in codes:
            code = code.strip().lower()
            # If already 2-letter code, use as-is
            if len(code) == 2:
                normalized.append(code)
            # If 3-letter code, map it
            elif code in mapping:
                normalized.append(mapping[code])
            # Otherwise, skip
            else:
                continue

        return normalized if normalized else ["hi", "en"]

    def _detect_language(self, text: str) -> str:
        """
        Detect primary language in text.

        Args:
            text: Extracted text

        Returns:
            Language code ("hi" or "en")
        """
        # Count Devanagari characters (Hindi)
        devanagari_count = sum(1 for c in text if "\u0900" <= c <= "\u097f")

        # If more than 10% Devanagari, likely Hindi
        if devanagari_count > len(text) * 0.1:
            return "hi"
        return "en"
