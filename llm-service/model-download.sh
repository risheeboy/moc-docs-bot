#!/bin/bash

# Model download script for LLM Service
# Pre-downloads model weights to model cache volume

set -e

echo "LLM Service - Model Download Script"
echo "===================================="

# Model IDs
LLAMA_MODEL="meta-llama/Llama-3.1-8B-Instruct-AWQ"
MISTRAL_MODEL="mistralai/Mistral-NeMo-Instruct-2407-AWQ"
GEMMA_MODEL="google/gemma-3-12b-it-awq"

# Download directory
DOWNLOAD_DIR="${HF_HOME:-.}/models"
mkdir -p "$DOWNLOAD_DIR"

echo "Download directory: $DOWNLOAD_DIR"
echo ""

# Function to download model
download_model() {
    local model_id=$1
    local model_name=$2

    echo "Downloading $model_name..."
    echo "Model ID: $model_id"

    python -c "
from huggingface_hub import snapshot_download
import sys

try:
    snapshot_download(
        repo_id='$model_id',
        local_dir='$DOWNLOAD_DIR/$model_name',
        repo_type='model',
        allow_patterns=['*.safetensors', '*.json', '*.tokenizer*'],
        ignore_patterns=['*.bin'],  # Skip .bin files (use .safetensors)
        revision='main',
        force_download=False
    )
    print(f'✓ Successfully downloaded $model_name')
except Exception as e:
    print(f'✗ Failed to download $model_name: {e}', file=sys.stderr)
    sys.exit(1)
"

    if [ $? -ne 0 ]; then
        echo "Failed to download $model_name"
        exit 1
    fi
    echo ""
}

# Check HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    echo "WARNING: HF_TOKEN not set. Some gated models may fail to download."
    echo "Set HF_TOKEN=your_token for access to gated models."
    echo ""
fi

# Download models
download_model "$LLAMA_MODEL" "llama-3.1-8b-instruct-awq"
download_model "$MISTRAL_MODEL" "mistral-nemo-instruct-awq"
download_model "$GEMMA_MODEL" "gemma-3-12b-it-awq"

echo "===================================="
echo "Model download complete!"
echo ""
echo "Models downloaded to: $DOWNLOAD_DIR"
echo "Total disk space used:"
du -sh "$DOWNLOAD_DIR"
