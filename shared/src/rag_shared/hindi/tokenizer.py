"""Hindi sentence and word tokenizer."""

import re
from typing import List, Optional


class HindiTokenizer:
    """Tokenizer for Hindi text."""

    # Sentence endings in Hindi (with optional trailing marks)
    SENTENCE_ENDINGS = {
        "।",  # Devanagari danda
        "॥",  # Devanagari double danda
        "।।",  # Double danda
        ".",
        "!",
        "?",
        "...",
    }

    # Hindi-specific abbreviations that don't end sentences
    ABBREVIATIONS = {
        "श्री",  # Sri/Mr
        "डॉ",  # Dr
        "इत्यादि",  # etc
        "आदि",  # and so on
    }

    # Common prefixes and suffixes (for word splitting)
    WORD_SEPARATORS = [
        r"\s+",  # Whitespace
        r"[,;:\-]",  # Punctuation
        r"(?<=[a-zA-Z0-9])(?=[ा-ौ])",  # Between consonant and vowel
    ]

    @classmethod
    def sentence_split(cls, text: str) -> List[str]:
        """Split Hindi text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text:
            return []

        # Add space after sentence-ending marks (except at end)
        for ending in cls.SENTENCE_ENDINGS:
            if ending in text:
                # Don't add space if already followed by space or quote
                text = re.sub(
                    f"({re.escape(ending)})(?!\\s|$|['\"])",
                    f"\\1 ",
                    text,
                )

        # Split on sentence boundaries
        # This regex handles multiple space characters after sentence ends
        sentences = re.split(r"[।॥.!?]+\s*", text)

        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @classmethod
    def word_tokenize(cls, text: str, remove_stopwords: bool = False) -> List[str]:
        """Tokenize Hindi text into words.

        Args:
            text: Input text
            remove_stopwords: Whether to remove common Hindi stopwords

        Returns:
            List of word tokens
        """
        if not text:
            return []

        # Split on separators
        words = re.split(r"[\s,;:\-._()\"'।॥]+", text)

        # Remove empty strings
        words = [w for w in words if w.strip()]

        # Optionally remove stopwords
        if remove_stopwords:
            from rag_shared.hindi.stopwords import HINDI_STOPWORDS

            words = [w for w in words if w.lower() not in HINDI_STOPWORDS]

        return words

    @classmethod
    def char_tokenize(cls, text: str) -> List[str]:
        """Tokenize text into individual characters.

        Args:
            text: Input text

        Returns:
            List of character tokens
        """
        return list(text)

    @classmethod
    def ngram_tokenize(cls, text: str, n: int = 2) -> List[str]:
        """Create n-gram tokens from text.

        Args:
            text: Input text
            n: N-gram size

        Returns:
            List of n-grams
        """
        words = cls.word_tokenize(text)

        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i : i + n])
            ngrams.append(ngram)

        return ngrams

    @classmethod
    def split_compounds(cls, word: str) -> List[str]:
        """Split compound Hindi words into components.

        Handles common compound patterns.

        Args:
            word: Hindi word to split

        Returns:
            List of component words
        """
        # Simple heuristic: split on common combining marks
        # This is a basic implementation - sophisticated splitting
        # would require morphological analysis

        # Split on common conjunct consonant markers
        components = re.split(r"्", word)

        return [c for c in components if c.strip()]


# Module-level convenience function
def tokenize_hindi(
    text: str,
    level: str = "word",
    remove_stopwords: bool = False,
) -> List[str]:
    """Tokenize Hindi text at specified level.

    Args:
        text: Hindi text to tokenize
        level: Tokenization level (sentence, word, char, ngram2, ngram3)
        remove_stopwords: Remove common words

    Returns:
        List of tokens
    """
    if level == "sentence":
        return HindiTokenizer.sentence_split(text)
    elif level == "word":
        return HindiTokenizer.word_tokenize(text, remove_stopwords)
    elif level == "char":
        return HindiTokenizer.char_tokenize(text)
    elif level == "ngram2":
        return HindiTokenizer.ngram_tokenize(text, n=2)
    elif level == "ngram3":
        return HindiTokenizer.ngram_tokenize(text, n=3)
    else:
        raise ValueError(f"Unknown tokenization level: {level}")
