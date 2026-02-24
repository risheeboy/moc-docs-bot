"""Data preparation for model training."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("data_preparer")


class DataPreparer:
    """Prepare and format data for training."""

    def __init__(self, output_dir: str = "/app/data/train"):
        """Initialize data preparer.

        Args:
            output_dir: Directory to save prepared data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_documents_to_instruction_format(
        self,
        documents: List[Dict[str, Any]],
        output_file: str = "instruction_dataset.jsonl",
    ) -> str:
        """Convert raw documents to instruction-tuning format.

        Args:
            documents: List of document dicts with 'title', 'content', 'source_url'
            output_file: Output filename

        Returns:
            Path to saved instruction dataset
        """
        output_path = self.output_dir / output_file
        instruction_count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for doc in documents:
                # Create instruction-following examples from document content
                instructions = self._extract_instructions_from_document(doc)

                for instruction in instructions:
                    f.write(json.dumps(instruction, ensure_ascii=False) + "\n")
                    instruction_count += 1

        logger.info(
            "Converted documents to instruction format",
            extra={
                "input_doc_count": len(documents),
                "output_instruction_count": instruction_count,
                "output_file": str(output_path),
            },
        )

        return str(output_path)

    def _extract_instructions_from_document(self, document: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract instruction examples from a document.

        Args:
            document: Document with title, content, metadata

        Returns:
            List of instruction-following examples
        """
        instructions = []
        content = document.get("content", "")
        title = document.get("title", "")
        source_url = document.get("source_url", "")

        if not content:
            return instructions

        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, paragraph in enumerate(paragraphs[:10]):  # Limit to 10 paragraphs per doc
            if len(paragraph.split()) < 10:
                continue

            # Create question-answering example
            example = {
                "instruction": f"Based on Ministry of Culture information: {title}, answer the following question.",
                "input": f"Question: Provide information about {self._extract_key_terms(paragraph)[:50]}",
                "output": paragraph,
                "metadata": {
                    "source": source_url,
                    "document_title": title,
                    "paragraph_index": i,
                },
            }
            instructions.append(example)

            # Create summarization example
            if len(paragraph.split()) > 50:
                summary_example = {
                    "instruction": "Summarize the following Ministry of Culture information.",
                    "input": paragraph,
                    "output": self._create_summary(paragraph),
                    "metadata": {
                        "source": source_url,
                        "document_title": title,
                        "task": "summarization",
                    },
                }
                instructions.append(summary_example)

        return instructions

    def _extract_key_terms(self, text: str) -> str:
        """Extract key terms from text.

        Args:
            text: Input text

        Returns:
            Key terms (first few words)
        """
        words = text.split()[:10]
        return " ".join(words)

    def _create_summary(self, text: str) -> str:
        """Create a simple summary by taking first sentences.

        Args:
            text: Input text

        Returns:
            Summary
        """
        sentences = text.split(".")[:3]
        return ". ".join([s.strip() for s in sentences if s.strip()]) + "."

    def format_qa_pairs(
        self,
        qa_pairs: List[Dict[str, Any]],
        output_file: str = "qa_dataset.jsonl",
    ) -> str:
        """Format QA pairs for training.

        Args:
            qa_pairs: List of QA pair dicts with 'question', 'answer'
            output_file: Output filename

        Returns:
            Path to saved QA dataset
        """
        output_path = self.output_dir / output_file
        saved_count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for qa in qa_pairs:
                formatted_qa = {
                    "instruction": "Answer the following question about Indian Ministry of Culture.",
                    "input": qa.get("question", ""),
                    "output": qa.get("answer", ""),
                    "metadata": {
                        "language": qa.get("language", "hi"),
                        "source_site": qa.get("source_site", ""),
                        "confidence": qa.get("confidence", 0.0),
                    },
                }
                f.write(json.dumps(formatted_qa, ensure_ascii=False) + "\n")
                saved_count += 1

        logger.info(
            "Formatted QA pairs for training",
            extra={
                "pair_count": saved_count,
                "output_file": str(output_path),
            },
        )

        return str(output_path)

    def split_dataset(
        self,
        input_file: str,
        train_ratio: float = 0.8,
        eval_ratio: float = 0.1,
        test_ratio: float = 0.1,
    ) -> Tuple[str, str, str]:
        """Split dataset into train/eval/test sets.

        Args:
            input_file: Path to input JSONL file
            train_ratio: Training set ratio
            eval_ratio: Evaluation set ratio
            test_ratio: Test set ratio

        Returns:
            Tuple of (train_path, eval_path, test_path)
        """
        input_path = Path(input_file)

        # Read all examples
        examples = []
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))

        total = len(examples)
        train_size = int(total * train_ratio)
        eval_size = int(total * eval_ratio)

        # Split
        train_examples = examples[:train_size]
        eval_examples = examples[train_size : train_size + eval_size]
        test_examples = examples[train_size + eval_size :]

        # Save splits
        train_path = self.output_dir / "train.jsonl"
        eval_path = self.output_dir / "eval.jsonl"
        test_path = self.output_dir / "test.jsonl"

        for path, examples_subset in [
            (train_path, train_examples),
            (eval_path, eval_examples),
            (test_path, test_examples),
        ]:
            with open(path, "w", encoding="utf-8") as f:
                for ex in examples_subset:
                    f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        logger.info(
            "Split dataset into train/eval/test",
            extra={
                "total_examples": total,
                "train_size": len(train_examples),
                "eval_size": len(eval_examples),
                "test_size": len(test_examples),
            },
        )

        return str(train_path), str(eval_path), str(test_path)

    def validate_dataset(self, dataset_path: str) -> bool:
        """Validate dataset format and structure.

        Args:
            dataset_path: Path to dataset JSONL file

        Returns:
            True if valid, False otherwise
        """
        required_keys = {"instruction", "input", "output"}
        valid_count = 0
        invalid_count = 0

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        example = json.loads(line)
                        if not all(key in example for key in required_keys):
                            logger.warning(
                                "Invalid example format",
                                extra={
                                    "line_number": line_num,
                                    "missing_keys": list(required_keys - set(example.keys())),
                                },
                            )
                            invalid_count += 1
                        else:
                            valid_count += 1
                    except json.JSONDecodeError as e:
                        logger.warning(
                            "Invalid JSON in dataset",
                            extra={"line_number": line_num, "error": str(e)},
                        )
                        invalid_count += 1

            logger.info(
                "Dataset validation complete",
                extra={
                    "valid_examples": valid_count,
                    "invalid_examples": invalid_count,
                    "dataset_path": dataset_path,
                },
            )

            return invalid_count == 0

        except Exception as e:
            logger.error(
                "Error validating dataset",
                extra={"dataset_path": dataset_path, "error": str(e)},
                exc_info=True,
            )
            return False
