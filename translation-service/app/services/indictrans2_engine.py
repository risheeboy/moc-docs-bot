"""IndicTrans2 translation engine"""

import asyncio
from typing import Optional

import structlog
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from app.config import settings

logger = structlog.get_logger()


class IndicTrans2Engine:
    """
    Wrapper around AI4Bharat IndicTrans2 model.

    Supports translation between 22 scheduled Indian languages + English.
    Uses CUDA GPU for inference if available.
    """

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self._initialized = False

    async def initialize(self):
        """Load the IndicTrans2 model and tokenizer"""
        if self._initialized:
            return

        logger.info(
            "Loading IndicTrans2 model",
            model=settings.translation_model,
        )

        try:
            # Check for GPU
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Using device for translation", device=self.device)

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.translation_model,
                trust_remote_code=True,
                cache_dir=settings.model_cache_dir,
            )

            # Load model
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                settings.translation_model,
                trust_remote_code=True,
                device_map=self.device,
                cache_dir=settings.model_cache_dir,
            )

            # Set model to eval mode
            self.model.eval()

            self._initialized = True
            logger.info("IndicTrans2 model loaded successfully")

        except Exception as e:
            logger.error("Failed to load IndicTrans2 model", error=str(e))
            raise

    async def cleanup(self):
        """Clean up GPU memory"""
        if self.model is not None:
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self._initialized = False
            logger.info("IndicTrans2 model cleaned up")

    async def health_check(self) -> bool:
        """Check if model is healthy and can perform inference"""
        if not self._initialized or self.model is None:
            return False

        try:
            # Quick inference test
            test_input = "health"
            inputs = self.tokenizer(
                test_input,
                return_tensors="pt",
                padding=True,
                truncation=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=128,
                    num_beams=1,
                )

            return True
        except Exception as e:
            logger.error("Model health check failed", error=str(e))
            return False

    async def translate(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        """
        Translate text from source language to target language.

        Uses IndicTrans2's language tag format:
        - English input: regular text
        - Indic input: prepended with language identifier token
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        # Format input text with language tags (IndicTrans2 expects specific format)
        if source_language != "en":
            # For Indic→English or Indic→Indic
            formatted_text = f"__translate_from_{source_language}_to_{target_language}__ {text}"
        else:
            # For English→Indic
            formatted_text = f"__translate_from_{source_language}_to_{target_language}__ {text}"

        try:
            # Tokenize
            inputs = self.tokenizer(
                formatted_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(self.device)

            # Generate translation
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    length_penalty=0.6,
                    early_stopping=True,
                )

            # Decode
            translated_text = self.tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )[0]

            return translated_text.strip()

        except Exception as e:
            logger.error(
                "Translation inference failed",
                error=str(e),
                source_language=source_language,
                target_language=target_language,
            )
            raise

    async def translate_batch(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> list[str]:
        """
        Translate multiple texts in batch.

        More efficient than calling translate() multiple times.
        """
        if not self._initialized:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        if not texts:
            return []

        # Format texts with language tags
        formatted_texts = []
        for text in texts:
            if source_language != "en":
                formatted_text = f"__translate_from_{source_language}_to_{target_language}__ {text}"
            else:
                formatted_text = f"__translate_from_{source_language}_to_{target_language}__ {text}"
            formatted_texts.append(formatted_text)

        try:
            # Tokenize all texts
            inputs = self.tokenizer(
                formatted_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(self.device)

            # Generate translations
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=4,
                    length_penalty=0.6,
                    early_stopping=True,
                )

            # Decode all outputs
            translations = self.tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )

            return [t.strip() for t in translations]

        except Exception as e:
            logger.error(
                "Batch translation inference failed",
                error=str(e),
                batch_size=len(texts),
                source_language=source_language,
                target_language=target_language,
            )
            raise


# Global singleton instance
indictrans2_engine = IndicTrans2Engine()
