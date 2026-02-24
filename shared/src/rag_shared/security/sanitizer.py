"""Input sanitization for XSS, injection attacks, and PII detection."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitizer for user input to prevent XSS and injection attacks.

    Per §6 of Shared Contracts: Never log PII (Aadhaar, phone, email).
    Use this sanitizer before logging user-provided text.
    """

    # PII patterns
    AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    PHONE_PATTERN = re.compile(r"\b(?:\+91|0)?[6-9]\d{9}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    AADHAR_PATTERN = re.compile(r"\b\d{12}\b")

    # XSS patterns
    SCRIPT_PATTERN = re.compile(r"<\s*script[^>]*>.*?</\s*script\s*>", re.IGNORECASE | re.DOTALL)
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
        re.compile(r"(\bor\b.*\b1\s*=\s*1\b)", re.IGNORECASE),
        re.compile(r"(;\s*drop\b)", re.IGNORECASE),
        re.compile(r"(;\s*delete\b)", re.IGNORECASE),
        re.compile(r"(;\s*update\b)", re.IGNORECASE),
    ]

    COMMAND_INJECTION_PATTERNS = [
        re.compile(r"([;&|`$(){}[\]<>])+"),  # Shell metacharacters
        re.compile(r"(rm\s+-rf|cat\s+/etc/passwd)"),  # Common commands
    ]

    @classmethod
    def sanitize(cls, text: str, allow_html: bool = False) -> str:
        """Sanitize user input.

        Args:
            text: Input text
            allow_html: If True, preserve safe HTML tags (default False)

        Returns:
            Sanitized text
        """
        if not text:
            return text

        # Remove script tags
        text = cls.SCRIPT_PATTERN.sub("", text)

        # Remove HTML tags if not allowed
        if not allow_html:
            text = cls.HTML_TAG_PATTERN.sub("", text)
        else:
            # At minimum, escape dangerous attributes
            text = re.sub(r'on\w+\s*=', "", text, flags=re.IGNORECASE)

        # Remove null bytes
        text = text.replace("\x00", "")

        return text.strip()

    @classmethod
    def remove_pii(cls, text: str) -> str:
        """Remove PII from text for safe logging.

        Replaces:
        - Aadhaar numbers → [AADHAAR]
        - Phone numbers → [PHONE]
        - Email addresses → [EMAIL]

        Args:
            text: Input text that may contain PII

        Returns:
            Text with PII removed
        """
        if not text:
            return text

        # Mask Aadhaar numbers (12 digits or 4-4-4)
        text = cls.AADHAAR_PATTERN.sub("[AADHAAR]", text)
        text = cls.AADHAR_PATTERN.sub("[AADHAAR]", text)

        # Mask phone numbers
        text = cls.PHONE_PATTERN.sub("[PHONE]", text)

        # Mask email addresses
        text = cls.EMAIL_PATTERN.sub("[EMAIL]", text)

        return text

    @classmethod
    def detect_sql_injection(cls, text: str) -> bool:
        """Detect potential SQL injection attempts.

        Args:
            text: Input to check

        Returns:
            True if potential SQL injection detected
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning(f"Potential SQL injection detected: {text[:50]}")
                return True
        return False

    @classmethod
    def detect_command_injection(cls, text: str) -> bool:
        """Detect potential command injection attempts.

        Args:
            text: Input to check

        Returns:
            True if potential command injection detected
        """
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if pattern.search(text):
                logger.warning(f"Potential command injection detected: {text[:50]}")
                return True
        return False

    @classmethod
    def is_safe(cls, text: str) -> bool:
        """Check if input is safe (no injection attacks).

        Args:
            text: Input to check

        Returns:
            True if input appears safe
        """
        return not (cls.detect_sql_injection(text) or cls.detect_command_injection(text))


# Convenience functions
def sanitize_input(text: str, allow_html: bool = False) -> str:
    """Sanitize user input.

    Args:
        text: Input text
        allow_html: If True, preserve safe HTML

    Returns:
        Sanitized text
    """
    return InputSanitizer.sanitize(text, allow_html)


def remove_pii(text: str) -> str:
    """Remove PII from text for logging.

    Args:
        text: Text that may contain PII

    Returns:
        Text with PII masked
    """
    return InputSanitizer.remove_pii(text)


def is_safe_input(text: str) -> bool:
    """Check if input is safe (no injection).

    Args:
        text: Input to check

    Returns:
        True if safe
    """
    return InputSanitizer.is_safe(text)
