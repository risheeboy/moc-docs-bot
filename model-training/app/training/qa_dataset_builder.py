"""Generate QA pairs from Ministry content using self-instruct."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("qa_dataset_builder")


class QADatasetBuilder:
    """Build QA pairs from Ministry of Culture documents using self-instruct approach."""

    def __init__(self, output_dir: str = "/app/data"):
        """Initialize QA dataset builder.

        Args:
            output_dir: Directory to save QA pairs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_qa_pairs_from_documents(
        self,
        documents: List[Dict[str, Any]],
        output_file: str = "ministry_qa_pairs.jsonl",
        min_qa_pairs_per_doc: int = 2,
    ) -> Tuple[str, int]:
        """Generate QA pairs from documents.

        Args:
            documents: List of document dicts
            output_file: Output filename
            min_qa_pairs_per_doc: Minimum QA pairs to generate per document

        Returns:
            Tuple of (output_path, total_qa_pairs_generated)
        """
        output_path = self.output_dir / output_file
        total_qa_pairs = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for doc in documents:
                qa_pairs = self._generate_qa_from_single_doc(doc)
                qa_pairs = qa_pairs[:10]  # Limit per document

                for qa in qa_pairs:
                    f.write(json.dumps(qa, ensure_ascii=False) + "\n")
                    total_qa_pairs += 1

        logger.info(
            "Generated QA pairs from documents",
            extra={
                "document_count": len(documents),
                "total_qa_pairs": total_qa_pairs,
                "output_file": str(output_path),
            },
        )

        return str(output_path), total_qa_pairs

    def _generate_qa_from_single_doc(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate QA pairs from a single document.

        Args:
            document: Document dict with title, content, metadata

        Returns:
            List of QA pair dicts
        """
        qa_pairs = []
        content = document.get("content", "")
        title = document.get("title", "")
        source_url = document.get("source_url", "")
        language = document.get("language", "hi")
        source_site = document.get("source_site", "")

        if not content or len(content.split()) < 20:
            return qa_pairs

        # Split into sentences
        sentences = self._split_into_sentences(content)

        # Generate different types of QA pairs
        qa_pairs.extend(self._generate_factual_qa(sentences, document))
        qa_pairs.extend(self._generate_definition_qa(sentences, document))
        qa_pairs.extend(self._generate_summary_qa(sentences, document))

        return qa_pairs

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitter (can be enhanced with NLTK)
        sentences = []
        for line in text.split("\n"):
            for sentence in line.split("."):
                sentence = sentence.strip()
                if sentence and len(sentence.split()) > 5:
                    sentences.append(sentence + ".")

        return sentences

    def _generate_factual_qa(
        self,
        sentences: List[str],
        document: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate factual QA pairs.

        Args:
            sentences: List of sentences
            document: Document metadata

        Returns:
            List of QA pairs
        """
        qa_pairs = []
        title = document.get("title", "")
        source_url = document.get("source_url", "")
        language = document.get("language", "hi")
        source_site = document.get("source_site", "")

        for i, sentence in enumerate(sentences[:5]):
            # Extract key entities (simple extraction)
            words = sentence.split()
            if len(words) < 10:
                continue

            # Create factual question
            key_phrase = " ".join(words[:5])
            qa_pair = {
                "question": f"What is mentioned about {key_phrase} in {title}?",
                "answer": sentence,
                "language": language,
                "source_site": source_site,
                "source_url": source_url,
                "qa_type": "factual",
                "confidence": 0.8,
            }
            qa_pairs.append(qa_pair)

        return qa_pairs

    def _generate_definition_qa(
        self,
        sentences: List[str],
        document: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate definition QA pairs.

        Args:
            sentences: List of sentences
            document: Document metadata

        Returns:
            List of QA pairs
        """
        qa_pairs = []
        title = document.get("title", "")
        source_url = document.get("source_url", "")
        language = document.get("language", "hi")
        source_site = document.get("source_site", "")

        # Generate definition questions for key topics
        key_topics = self._extract_key_topics(title)

        for topic in key_topics[:3]:
            relevant_sentence = self._find_relevant_sentence(sentences, topic)
            if relevant_sentence:
                qa_pair = {
                    "question": f"Define or explain {topic} in the context of {title}.",
                    "answer": relevant_sentence,
                    "language": language,
                    "source_site": source_site,
                    "source_url": source_url,
                    "qa_type": "definition",
                    "confidence": 0.75,
                }
                qa_pairs.append(qa_pair)

        return qa_pairs

    def _generate_summary_qa(
        self,
        sentences: List[str],
        document: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate summary QA pairs.

        Args:
            sentences: List of sentences
            document: Document metadata

        Returns:
            List of QA pairs
        """
        qa_pairs = []
        title = document.get("title", "")
        source_url = document.get("source_url", "")
        language = document.get("language", "hi")
        source_site = document.get("source_site", "")

        if len(sentences) > 0:
            # Create summary from first few sentences
            summary = " ".join(sentences[:3])
            if len(summary.split()) > 50:
                qa_pair = {
                    "question": f"Summarize the key points about {title}.",
                    "answer": summary,
                    "language": language,
                    "source_site": source_site,
                    "source_url": source_url,
                    "qa_type": "summary",
                    "confidence": 0.7,
                }
                qa_pairs.append(qa_pair)

        return qa_pairs

    def _extract_key_topics(self, title: str) -> List[str]:
        """Extract key topics from title.

        Args:
            title: Document title

        Returns:
            List of key topics
        """
        # Simple extraction - can be enhanced
        words = title.split()
        return [" ".join(words[i : i + 2]) for i in range(0, len(words) - 1, 2)][:5]

    def _find_relevant_sentence(self, sentences: List[str], topic: str) -> Optional[str]:
        """Find sentence relevant to topic.

        Args:
            sentences: List of sentences
            topic: Topic to find

        Returns:
            Relevant sentence or None
        """
        topic_lower = topic.lower()
        for sentence in sentences:
            if topic_lower in sentence.lower():
                return sentence

        return sentences[0] if sentences else None

    def generate_hindi_specific_qa(
        self,
        documents: List[Dict[str, Any]],
        output_file: str = "hindi_qa_pairs.jsonl",
    ) -> Tuple[str, int]:
        """Generate Hindi-specific QA pairs with Hindi questions and answers.

        Args:
            documents: List of document dicts (preferably in Hindi)
            output_file: Output filename

        Returns:
            Tuple of (output_path, total_qa_pairs_generated)
        """
        output_path = self.output_dir / output_file
        total_qa_pairs = 0

        hindi_documents = [d for d in documents if d.get("language") == "hi"]

        with open(output_path, "w", encoding="utf-8") as f:
            for doc in hindi_documents:
                # For Hindi, we'll use the content as-is since it's already in Hindi
                content = doc.get("content", "")
                title = doc.get("title", "")
                source_url = doc.get("source_url", "")
                source_site = doc.get("source_site", "")

                if not content or len(content.split()) < 20:
                    continue

                sentences = self._split_into_sentences(content)

                # Create Hindi QA pairs
                for i, sentence in enumerate(sentences[:5]):
                    qa = {
                        "question": f"{title} के बारे में क्या कहा गया है?",
                        "answer": sentence,
                        "language": "hi",
                        "source_site": source_site,
                        "source_url": source_url,
                        "qa_type": "factual",
                        "confidence": 0.8,
                    }
                    f.write(json.dumps(qa, ensure_ascii=False) + "\n")
                    total_qa_pairs += 1

        logger.info(
            "Generated Hindi-specific QA pairs",
            extra={
                "hindi_document_count": len(hindi_documents),
                "total_qa_pairs": total_qa_pairs,
                "output_file": str(output_path),
            },
        )

        return str(output_path), total_qa_pairs

    def merge_qa_datasets(
        self,
        qa_files: List[str],
        output_file: str = "merged_qa_pairs.jsonl",
    ) -> Tuple[str, int]:
        """Merge multiple QA datasets.

        Args:
            qa_files: List of JSONL file paths
            output_file: Output filename

        Returns:
            Tuple of (output_path, total_qa_pairs)
        """
        output_path = self.output_dir / output_file
        total_qa_pairs = 0

        with open(output_path, "w", encoding="utf-8") as out_f:
            for qa_file in qa_files:
                try:
                    with open(qa_file, "r", encoding="utf-8") as in_f:
                        for line in in_f:
                            if line.strip():
                                out_f.write(line)
                                total_qa_pairs += 1
                except Exception as e:
                    logger.warning(
                        "Error reading QA file",
                        extra={"file": qa_file, "error": str(e)},
                    )

        logger.info(
            "Merged QA datasets",
            extra={
                "input_files": len(qa_files),
                "total_qa_pairs": total_qa_pairs,
                "output_file": str(output_path),
            },
        )

        return str(output_path), total_qa_pairs
