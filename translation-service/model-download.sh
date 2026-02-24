#!/bin/bash

# Download model weights for IndicTrans2
# This script is run during Docker image build time to pre-cache model weights

set -e

echo "Downloading IndicTrans2 model weights..."

# Create cache directory
mkdir -p /root/.cache/huggingface/hub

# Download the model and tokenizer
python3 << 'EOF'
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "ai4bharat/indictrans2-indic-en-1B"
cache_dir = "/root/.cache/huggingface/hub"

print(f"Downloading model: {model_name}")
print(f"Cache directory: {cache_dir}")

try:
    # Download tokenizer
    print("Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=cache_dir,
    )
    print("Tokenizer downloaded successfully")

    # Download model
    print("Downloading model weights...")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=cache_dir,
    )
    print("Model weights downloaded successfully")

    print(f"Model successfully cached in {cache_dir}")

except Exception as e:
    print(f"Error downloading model: {e}")
    exit(1)
EOF

echo "Model weights downloaded successfully"
