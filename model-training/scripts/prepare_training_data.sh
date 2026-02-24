#!/bin/bash

# Prepare training data for model fine-tuning

set -e

echo "Preparing training data for model fine-tuning..."

# Create necessary directories
mkdir -p /app/data/train
mkdir -p /app/data/eval
mkdir -p /app/data/feedback
mkdir -p /tmp/logs

# Check if raw documents exist
if [ ! -d "/app/data/raw_documents" ]; then
    echo "Warning: Raw documents directory not found at /app/data/raw_documents"
    echo "Please ensure scraped documents are available"
fi

# Run data preparation Python script
python -c "
import sys
import json
from pathlib import Path
from app.training.data_preparer import DataPreparer
from app.training.qa_dataset_builder import QADatasetBuilder

print('Loading raw documents...')

# Load raw documents from MinIO or local storage
documents = []
raw_doc_dir = Path('/app/data/raw_documents')

if raw_doc_dir.exists():
    for doc_file in raw_doc_dir.glob('*.json'):
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                documents.append(doc)
        except Exception as e:
            print(f'Error loading {doc_file}: {e}', file=sys.stderr)

print(f'Loaded {len(documents)} documents')

# Initialize preparers
preparer = DataPreparer('/app/data/train')
qa_builder = QADatasetBuilder('/app/data')

# Convert documents to instruction format
if documents:
    print('Converting documents to instruction format...')
    instruction_file = preparer.convert_documents_to_instruction_format(documents)
    print(f'Generated instruction dataset: {instruction_file}')

    # Generate QA pairs
    print('Generating QA pairs...')
    qa_file, qa_count = qa_builder.generate_qa_pairs_from_documents(documents)
    print(f'Generated {qa_count} QA pairs')

    # Generate Hindi-specific QA pairs
    print('Generating Hindi-specific QA pairs...')
    hindi_qa_file, hindi_count = qa_builder.generate_hindi_specific_qa(documents)
    print(f'Generated {hindi_count} Hindi QA pairs')

    # Merge and validate
    print('Merging datasets...')
    merged_file, total = qa_builder.merge_qa_datasets([qa_file, hindi_qa_file])
    print(f'Merged dataset contains {total} QA pairs')

    # Validate dataset
    print('Validating dataset...')
    if preparer.validate_dataset(merged_file):
        print('Dataset validation passed!')
    else:
        print('Warning: Some invalid examples found in dataset', file=sys.stderr)

    # Split into train/eval
    print('Splitting into train/eval/test sets...')
    train_file, eval_file, test_file = preparer.split_dataset(merged_file)
    print(f'Train set: {train_file}')
    print(f'Eval set: {eval_file}')
    print(f'Test set: {test_file}')

else:
    print('No documents found. Skipping data preparation.', file=sys.stderr)
"

echo "Data preparation complete!"
