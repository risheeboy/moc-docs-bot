"""Tesseract OCR Engine for Hindi and English."""

from typing import Optional, Any
import pytesseract
from PIL import Image
import structlog
import re

from app.config import settings
from app.services.preprocessor import ImagePreprocessor
from app.services.postprocessor import PostProcessor
from app.services.layout_analyzer import LayoutAnalyzer

logger = structlog.get_logger()


class TesseractOCREngine:
    """Tesseract-based OCR engine for Hindi and English."""

    def __init__(self):
        """Initialize Tesseract engine."""
        self.preprocessor = ImagePreprocessor(
            enable_deskew=settings.deskew_enabled,
            enable_denoise=settings.denoise_enabled,
            enable_binarize=settings.binarize_enabled,
        )
        self.postprocessor = PostProcessor()
        self.layout_analyzer = LayoutAnalyzer()

    def process(
        self,
        image: Image.Image,
        languages: str,
        page_number: int = 1,
    ) -> dict[str, Any]:
        """
        Process image with Tesseract OCR.

        Args:
            image: PIL Image
            languages: Language codes (e.g., "hin+eng" or "hi,en")
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

            # Convert language format if needed
            tesseract_langs = self._normalize_languages(languages)

            # Extract text and detailed data
            logger.info(
                "tesseract_processing",
                languages=tesseract_langs,
                page_number=page_number,
            )

            # Get detailed output with confidence
            data = pytesseract.image_to_data(
                processed_image,
                lang=tesseract_langs,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",  # PSM 6: Assume single uniform block
            )

            # Extract full text
            full_text = pytesseract.image_to_string(
                processed_image,
                lang=tesseract_langs,
                config="--psm 6",
            )

            # Post-process text (fix Hindi ligatures, etc.)
            full_text = self.postprocessor.postprocess(full_text, languages)

            # Analyze layout and extract regions
            regions = self._extract_regions(data, processed_image)

            # Calculate overall confidence
            confidences = [r["confidence"] for r in regions if r.get("confidence")]
            overall_confidence = (
                sum(confidences) / len(confidences)
                if confidences
                else pytesseract.image_to_data(
                    processed_image,
                    lang=tesseract_langs,
                    output_type=pytesseract.Output.DICT,
                ).get("conf", [0])
            )

            result = {
                "page_number": page_number,
                "text": full_text,
                "regions": regions,
                "confidence": min(overall_confidence / 100.0, 1.0)
                if isinstance(overall_confidence, (int, float))
                else 0.7,
                "language": self._detect_language(full_text),
                "engine": "tesseract",
            }

            logger.info(
                "tesseract_processing_complete",
                page_number=page_number,
                num_regions=len(regions),
                confidence=result["confidence"],
            )

            return result

        except Exception as e:
            logger.error(
                "tesseract_processing_error",
                error=str(e),
                page_number=page_number,
            )
            raise

    def _extract_regions(self, data: dict, image: Image.Image) -> list[dict]:
        """
        Extract text regions from Tesseract output.

        Args:
            data: Tesseract image_to_data output
            image: Original PIL image

        Returns:
            List of region dicts with text, bbox, confidence
        """
        regions = []
        img_width, img_height = image.size

        # Group data by line
        lines = {}
        for i, text in enumerate(data.get("text", [])):
            if not text.strip():
                continue

            line_num = data["line_num"][i]
            if line_num not in lines:
                lines[line_num] = {
                    "text": [],
                    "boxes": [],
                    "confidences": [],
                }

            lines[line_num]["text"].append(text)
            lines[line_num]["boxes"].append(
                (
                    data["left"][i],
                    data["top"][i],
                    data["left"][i] + data["width"][i],
                    data["top"][i] + data["height"][i],
                )
            )
            conf = int(data.get("conf", [0])[i])
            if conf >= 0:
                lines[line_num]["confidences"].append(conf / 100.0)

        # Convert lines to regions
        for line_num in sorted(lines.keys()):
            line_data = lines[line_num]
            if not line_data["text"]:
                continue

            # Combine text
            text = " ".join(line_data["text"])

            # Combine bounding boxes
            if line_data["boxes"]:
                x1 = min(box[0] for box in line_data["boxes"])
                y1 = min(box[1] for box in line_data["boxes"])
                x2 = max(box[2] for box in line_data["boxes"])
                y2 = max(box[3] for box in line_data["boxes"])

                # Clamp to image bounds
                x1 = max(0, min(x1, img_width))
                y1 = max(0, min(y1, img_height))
                x2 = max(0, min(x2, img_width))
                y2 = max(0, min(y2, img_height))

                confidence = (
                    sum(line_data["confidences"]) / len(line_data["confidences"])
                    if line_data["confidences"]
                    else 0.5
                )

                regions.append(
                    {
                        "text": text,
                        "bounding_box": [x1, y1, x2, y2],
                        "confidence": confidence,
                        "type": "paragraph",
                    }
                )

        return regions

    def _normalize_languages(self, languages: str) -> str:
        """
        Normalize language codes for Tesseract.

        Tesseract uses "hin", "eng", etc. or "hin+eng" format.

        Args:
            languages: Language codes (e.g., "hi,en" or "hin+eng")

        Returns:
            Normalized for Tesseract (e.g., "hin+eng")
        """
        mapping = {
            "hi": "hin",
            "en": "eng",
            "bn": "ben",
            "te": "tel",
            "mr": "mar",
            "ta": "tam",
            "ur": "urd",
            "gu": "guj",
            "kn": "kan",
            "ml": "mal",
            "or": "ory",
            "pa": "pan",
        }

        # Split by comma or plus
        codes = re.split(r"[,+]", languages.strip())
        normalized = []

        for code in codes:
            code = code.strip().lower()
            if code in mapping:
                normalized.append(mapping[code])
            elif len(code) == 3:
                normalized.append(code)

        return "+".join(normalized) if normalized else "hin+eng"

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
