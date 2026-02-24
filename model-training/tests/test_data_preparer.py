"""Tests for data preparation module."""

import json
import tempfile
from pathlib import Path

import pytest

from app.training.data_preparer import DataPreparer


@pytest.fixture
def sample_documents():
    """Provide sample documents for testing."""
    return [
        {
            "title": "About Ministry of Culture",
            "content": "The Ministry of Culture is responsible for promoting Indian heritage and culture. " * 10,
            "source_url": "https://culture.gov.in/about",
            "language": "en",
        },
        {
            "title": "भारतीय संस्कृति मंत्रालय",
            "content": "भारतीय संस्कृति मंत्रालय भारतीय विरासत को बढ़ावा देता है। " * 10,
            "source_url": "https://culture.gov.in/hi/about",
            "language": "hi",
        },
    ]


def test_convert_documents_to_instruction_format(sample_documents):
    """Test document to instruction format conversion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preparer = DataPreparer(tmpdir)
        output_file = preparer.convert_documents_to_instruction_format(
            sample_documents,
            "test_instructions.jsonl",
        )

        assert Path(output_file).exists()

        # Verify output format
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 0

            for line in lines:
                example = json.loads(line)
                assert "instruction" in example
                assert "input" in example
                assert "output" in example


def test_split_dataset(sample_documents):
    """Test dataset splitting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preparer = DataPreparer(tmpdir)

        # Create sample dataset
        dataset_file = Path(tmpdir) / "test_dataset.jsonl"
        with open(dataset_file, "w", encoding="utf-8") as f:
            for i in range(100):
                example = {
                    "instruction": "Test instruction",
                    "input": f"Input {i}",
                    "output": f"Output {i}",
                }
                f.write(json.dumps(example) + "\n")

        train_file, eval_file, test_file = preparer.split_dataset(str(dataset_file))

        # Check that splits exist
        assert Path(train_file).exists()
        assert Path(eval_file).exists()
        assert Path(test_file).exists()

        # Verify split sizes
        def count_lines(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return len([line for line in f if line.strip()])

        train_count = count_lines(train_file)
        eval_count = count_lines(eval_file)
        test_count = count_lines(test_file)

        assert train_count == 80
        assert eval_count == 10
        assert test_count == 10


def test_validate_dataset(sample_documents):
    """Test dataset validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preparer = DataPreparer(tmpdir)

        # Create valid dataset
        valid_file = Path(tmpdir) / "valid_dataset.jsonl"
        with open(valid_file, "w", encoding="utf-8") as f:
            example = {
                "instruction": "Test",
                "input": "Input",
                "output": "Output",
            }
            f.write(json.dumps(example) + "\n")

        # Validate should pass
        assert preparer.validate_dataset(str(valid_file))

        # Create invalid dataset
        invalid_file = Path(tmpdir) / "invalid_dataset.jsonl"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write('{"incomplete": "data"}\n')

        # Validate should fail
        assert not preparer.validate_dataset(str(invalid_file))
