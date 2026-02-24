# Model Training Service (Stream 14)

## Overview

Model Training & Evaluation Pipeline for domain-adapted LLMs on Ministry of Culture data. This service implements QLoRA fine-tuning, comprehensive evaluation benchmarks, and continuous learning mechanisms.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Model Training Service (Port 8007)             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  FastAPI Application                                   │
│  ├── /health (status & dependencies)                  │
│  ├── /metrics (Prometheus)                            │
│  ├── /finetune/start (POST)                           │
│  ├── /finetune/status (GET)                           │
│  └── /evaluate (POST)                                 │
│                                                         │
│  Training Pipeline                                      │
│  ├── DataPreparer: Document → Instruction format      │
│  ├── QADatasetBuilder: Self-instruct QA pair gen.    │
│  ├── LoRATrainer: QLoRA fine-tuning (PEFT)          │
│  └── ModelMerger: Merge adapters back                │
│                                                         │
│  Evaluation Suite                                       │
│  ├── HindiQAEval: Exact match, F1, BLEU              │
│  ├── HallucinationDetector: Fact checking            │
│  ├── ResponseQuality: LLM-as-judge                   │
│  └── BenchmarkSuite: Comprehensive eval              │
│                                                         │
│  Continuous Learning                                   │
│  ├── FeedbackCollector: User feedback ingestion      │
│  ├── DataDriftDetector: Content divergence            │
│  └── RetrainScheduler: Periodic retraining           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Features

### 1. QLoRA Fine-Tuning
- **4-bit Quantization**: Memory-efficient fine-tuning on single GPU
- **LoRA Rank Adaptation**: Low-rank updates with configurable rank (default 16)
- **Support for Multiple Models**:
  - Llama 3.1 8B Instruct (standard)
  - Mistral NeMo 12B (long-context)
  - Gemma 3 (multimodal-capable)

### 2. Data Preparation
- Convert raw documents to instruction-tuning format
- Auto-generate QA pairs using self-instruct
- Hindi-specific QA pair generation
- Dataset validation and splitting (train/eval/test)

### 3. Comprehensive Evaluation
- **QA Metrics**: Exact Match, F1, BLEU
- **Hindi-Specific**: Devanagari consistency, script validation
- **Hallucination Detection**: Fact-checking against sources
- **Response Quality**: LLM-as-judge evaluation (relevance, correctness, completeness)
- **Batch Evaluation**: Process multiple samples efficiently

### 4. Continuous Learning
- **Feedback Collection**: Capture user corrections and ratings
- **Negative Sampling**: Convert low-rated responses for retraining
- **Data Drift Detection**: Monitor content divergence from training data
- **Scheduled Retraining**: Automatic periodic fine-tuning

## Installation

### Build Docker Image

```bash
docker build -t model-training:latest .
```

### Run Container

```bash
docker run -d \
  --name model-training \
  --gpus all \
  -p 8007:8007 \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e TRAINING_LORA_RANK=16 \
  -e TRAINING_LEARNING_RATE=2e-4 \
  -e TRAINING_EPOCHS=3 \
  -v model-cache:/models \
  model-training:latest
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8007/health
```

### Start Fine-Tuning

```bash
curl -X POST http://localhost:8007/finetune/start \
  -H "Content-Type: application/json" \
  -d '{
    "base_model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "dataset_path": "s3://models/training_data/ministry_qa.jsonl",
    "hyperparameters": {
      "lora_rank": 16,
      "learning_rate": 0.0002,
      "epochs": 3,
      "batch_size": 4
    }
  }'
```

### Get Training Status

```bash
curl http://localhost:8007/finetune/status?job_id=<job_id>
```

### Run Evaluation

```bash
curl -X POST http://localhost:8007/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "model_version": "v1.0-finetuned",
    "eval_dataset": "s3://models/eval_data/hindi_qa_bench.jsonl",
    "metrics": ["exact_match", "f1", "bleu", "hallucination_rate"],
    "source_documents": "s3://models/eval_data/sources.json"
  }'
```

## Data Directory Structure

```
/app/data/
├── train/                          # Training datasets
│   ├── train.jsonl                 # Training split
│   ├── eval.jsonl                  # Evaluation split
│   └── test.jsonl                  # Test split
├── eval/                           # Evaluation data
│   ├── hindi_qa_bench.jsonl        # Hindi QA benchmark
│   └── sources.json                # Source documents
├── feedback/                       # User feedback
│   ├── feedback_*.json             # Individual feedback records
│   └── aggregated_feedback.json    # Aggregated stats
└── ministry_qa_pairs.jsonl         # Generated QA pairs
```

## MinIO Paths

```
models/
├── base/
│   ├── llama-3.1-8b-instruct-awq/
│   ├── mistral-nemo-instruct-awq/
│   └── gemma-3-12b-it-awq/
├── finetuned/
│   └── {model_id}/{version}/       # Fine-tuned adapters
├── training_data/
│   └── ministry_qa_v2.jsonl        # Training datasets
└── eval_data/
    └── hindi_qa_bench.jsonl        # Evaluation datasets
```

## Configuration

### Environment Variables

```bash
# Training Hyperparameters
TRAINING_LORA_RANK=16
TRAINING_LORA_ALPHA=32
TRAINING_LEARNING_RATE=2e-4
TRAINING_EPOCHS=3
TRAINING_BATCH_SIZE=4
TRAINING_MAX_SEQ_LENGTH=2048

# Model Selection
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<key>

# Continuous Learning
FEEDBACK_COLLECTION_ENABLED=true
RETRAIN_TRIGGER_THRESHOLD=100      # Number of negative samples
DATA_DRIFT_WINDOW_DAYS=30
RETRAIN_SCHEDULE_INTERVAL_HOURS=168  # 1 week
```

## Scripts

### Prepare Training Data

```bash
./scripts/prepare_training_data.sh
```

### Run Fine-Tuning

```bash
./scripts/run_finetune.sh \
  meta-llama/Llama-3.1-8B-Instruct-AWQ \
  /app/data/train/train.jsonl
```

### Run Evaluation

```bash
./scripts/run_eval.sh \
  /app/data/eval/eval.jsonl \
  /app/data/eval/sources.json
```

## Metrics & Monitoring

### Prometheus Metrics

- `training_jobs_total`: Total training jobs by status
- `training_duration_seconds`: Training job duration
- `training_loss_current`: Current training loss
- `evaluation_jobs_total`: Total evaluation jobs
- `evaluation_metric_value`: Evaluation metric values
- `gpu_memory_utilization_percent`: GPU memory usage

### Health Check Response

```json
{
  "status": "healthy",
  "service": "model-training",
  "version": "1.0.0",
  "uptime_seconds": 3612,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "gpu": { "status": "healthy", "device_count": 1, "latency_ms": 5 },
    "redis": { "status": "healthy", "latency_ms": 2 },
    "minio": { "status": "healthy", "latency_ms": 15 }
  }
}
```

## Evaluation Reports

Benchmarks generate three types of reports:

### 1. JSON Report
Complete metrics in machine-readable format
```bash
/tmp/eval_reports/{job_id}/results.json
```

### 2. Markdown Report
Human-readable evaluation summary
```bash
/tmp/eval_reports/{job_id}/report.md
```

### 3. HTML Report
Interactive visualizations and charts
```bash
/tmp/eval_reports/{job_id}/report.html
```

## Continuous Learning Workflow

```
1. User Feedback Collection
   ├── Query + Response + Rating
   └── Optional: Corrected Response

2. Feedback Aggregation
   ├── Collect negative samples (rating < 3)
   └── Generate retraining dataset

3. Data Drift Detection
   ├── Compare new documents with training baseline
   └── Trigger retraining if drift > threshold

4. Retraining Scheduler
   ├── Check for due jobs
   ├── Merge feedback + new data
   └── Trigger fine-tuning job

5. Evaluation & Deployment
   ├── Run benchmark suite
   ├── Compare with baseline model
   └── Deploy if metrics improve
```

## Development & Testing

### Run Tests

```bash
pytest tests/ -v
```

### Run with Debug Logging

```bash
export APP_DEBUG=true
export APP_LOG_LEVEL=DEBUG
python -m app.main
```

## Performance Notes

- **GPU Requirements**: RTX 3090 / A100 / H100 with 24GB+ VRAM
- **Training Time**: ~4-8 hours for 3 epochs on 10K examples (with gradient accumulation)
- **Model Size**: ~8-12GB after quantization
- **Inference Throughput**: ~10-20 tokens/second on RTX 3090

## Dependencies

- PyTorch 2.1+ with CUDA 12.1
- Transformers 4.36+
- PEFT 0.7+ (for LoRA)
- Datasets 2.15+
- Langfuse 2.56+ (observability)

## Architecture Compliance

This service complies with:
- ✅ Stream 14 specification (Model Fine-Tuning & Evaluation)
- ✅ Shared Contracts (§1-18 from 01_Shared_Contracts.md)
- ✅ API Schema (§8.7 endpoints)
- ✅ MinIO paths (§16)
- ✅ Error format (§4)
- ✅ Health checks (§5)
- ✅ Logging (§6)

## Future Enhancements

- [ ] Multi-GPU training with distributed training
- [ ] Adapter composition for ensemble models
- [ ] Automated hyperparameter tuning
- [ ] Model interpretability and attention visualization
- [ ] A/B testing framework for model comparison
- [ ] Integration with Langfuse for detailed tracing

## Support

For issues or questions, refer to:
- Implementation Plan: `Implementation_Plan/Stream_14_Model_Training.md`
- Shared Contracts: `Implementation_Plan/01_Shared_Contracts.md`
- Design Document: Main RAG system documentation
