#!/bin/bash

# Run model fine-tuning job

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <base_model> <dataset_path> [output_dir]"
    echo ""
    echo "Example:"
    echo "  $0 meta-llama/Llama-3.1-8B-Instruct-AWQ /app/data/train/train.jsonl"
    exit 1
fi

BASE_MODEL=$1
DATASET_PATH=$2
OUTPUT_DIR=${3:-/tmp/models}

echo "Starting fine-tuning..."
echo "Base Model: $BASE_MODEL"
echo "Dataset: $DATASET_PATH"
echo "Output: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run fine-tuning
python -c "
import sys
from pathlib import Path
from app.training.lora_trainer import LoRATrainer
from app.training.training_config import get_default_training_config

print('Initializing fine-tuning...')

# Create training config
config = get_default_training_config(
    model_name='$BASE_MODEL',
    output_dir='$OUTPUT_DIR',
    train_dataset_path='$DATASET_PATH',
)

# Initialize trainer
trainer = LoRATrainer(config)

# Load model and tokenizer
print('Loading model and tokenizer...')
trainer.prepare_model_and_tokenizer()

# Load dataset
print('Loading dataset...')
dataset = trainer.load_dataset('$DATASET_PATH')

# Preprocess dataset
print('Preprocessing dataset...')
train_dataset = trainer.preprocess_dataset(dataset)

# Run training
print('Starting training...')
result = trainer.train(train_dataset)

if result['status'] == 'completed':
    print(f'Training completed successfully!')
    print(f'Final loss: {result.get(\"training_loss\", \"N/A\")}')
    print(f'Duration: {result.get(\"duration_seconds\", \"N/A\")} seconds')
else:
    print(f'Training failed: {result.get(\"error\", \"Unknown error\")}', file=sys.stderr)
    sys.exit(1)
"

echo "Fine-tuning complete!"
