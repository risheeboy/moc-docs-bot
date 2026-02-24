# Model Training Service

FastAPI on port 8007. QLoRA fine-tuning for continuous model improvement (GPU-required, g5.2xlarge minimum).

## Key Files

- `app/main.py` — FastAPI application
- `app/services/trainer.py` — QLoRA training pipeline
- `app/services/evaluator.py` — Domain benchmark evaluation
- `app/services/data_processor.py` — Training data preparation
- `app/services/model_uploader.py` — Model upload to S3 registry
- `app/routers/` — Training endpoints, job management
- `app/config.py` — QLoRA hyperparameters

## Endpoints

- `POST /train/start` — Start fine-tuning job
- `GET /train/job/{job_id}` — Training job status
- `POST /evaluate` — Evaluate model on benchmarks
- `POST /deploy/model/{version}` — Deploy trained model to production
- `GET /health` — Health check

## Training Configuration

- LoRA rank: 16, alpha: 32
- Learning rate: 2e-4, warmup: 500 steps
- Batch size: 8 (per GPU), gradient accumulation: 4
- Max epochs: 3

## Base Models

Llama 3.1 8B, Mistral NeMo 12B, Gemma 3 12B (all AWQ 4-bit).

## Training Data

- Feedback table (human ratings)
- Conversation logs (approved samples)
- Curated Hindi cultural domain datasets
- RLHF signals (if available)

## Evaluation Benchmarks

- Hindi QA accuracy (domain-specific)
- Translation BLEU score
- Toxicity FP rate
- PII detection recall/precision

## Dependencies

- transformers, peft (QLoRA)
- torch (GPU), datasets
- wandb (optional monitoring)

## Known Issues

1. **Config case sensitivity bug** — `case_sensitive=True` breaks env var parsing.
2. **No S3 auto-upload** — Fine-tuned models lost on instance termination. Add save_to_s3().
3. **No rollback mechanism** — Can't revert to previous model if performance degrades.
