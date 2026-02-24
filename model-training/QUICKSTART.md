# Quick Start Guide - Model Training Service

## 1. Build and Run

### Build Docker Image
```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi/model-training
docker build -t model-training:latest .
```

### Run with Docker Compose
```yaml
# Add to docker-compose.yml:
model-training:
  image: model-training:latest
  container_name: model-training
  ports:
    - "8007:8007"
  environment:
    - APP_ENV=production
    - CUDA_VISIBLE_DEVICES=0
    - TRAINING_LORA_RANK=16
    - TRAINING_LEARNING_RATE=0.0002
    - TRAINING_EPOCHS=3
    - TRAINING_BATCH_SIZE=4
    - LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
    - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
    - REDIS_HOST=redis
    - POSTGRES_HOST=postgres
  volumes:
    - model-cache:/models
    - /app/data:/app/data
  networks:
    - rag-network
  depends_on:
    - redis
    - minio
    - postgres
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Run Locally (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CUDA_VISIBLE_DEVICES=0
export APP_ENV=development
export APP_LOG_LEVEL=DEBUG

# Run FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 --reload
```

## 2. Health Check

```bash
curl http://localhost:8007/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "model-training",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "gpu": {"status": "healthy", "device_count": 1},
    "redis": {"status": "healthy", "latency_ms": 2},
    "minio": {"status": "healthy", "latency_ms": 15}
  }
}
```

## 3. Prepare Training Data

### Option A: Using Script
```bash
./scripts/prepare_training_data.sh
```

This will:
1. Load documents from `/app/data/raw_documents`
2. Convert to instruction format
3. Generate QA pairs
4. Split into train/eval/test sets

### Option B: Manual Python
```python
from app.training.data_preparer import DataPreparer
from app.training.qa_dataset_builder import QADatasetBuilder
import json

# Load documents
documents = []
with open('documents.jsonl', 'r') as f:
    for line in f:
        documents.append(json.loads(line))

# Prepare data
preparer = DataPreparer('/app/data/train')
instruction_file = preparer.convert_documents_to_instruction_format(documents)

# Build QA pairs
qa_builder = QADatasetBuilder('/app/data')
qa_file, count = qa_builder.generate_qa_pairs_from_documents(documents)
print(f"Generated {count} QA pairs")

# Split dataset
train_file, eval_file, test_file = preparer.split_dataset(qa_file)
```

## 4. Start Fine-Tuning

### Via API
```bash
curl -X POST http://localhost:8007/finetune/start \
  -H "Content-Type: application/json" \
  -d '{
    "base_model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
    "dataset_path": "/app/data/train/train.jsonl",
    "hyperparameters": {
      "lora_rank": 16,
      "learning_rate": 0.0002,
      "epochs": 3,
      "batch_size": 4
    }
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "estimated_duration_minutes": 120,
  "created_at": "2026-02-24T10:30:00Z"
}
```

### Check Status
```bash
curl http://localhost:8007/finetune/status?job_id=550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.35,
  "training_loss": 2.15,
  "eval_loss": 2.42,
  "steps_completed": 350,
  "total_steps": 1000,
  "elapsed_seconds": 1800,
  "estimated_remaining_seconds": 3600
}
```

### Via Script
```bash
./scripts/run_finetune.sh \
  meta-llama/Llama-3.1-8B-Instruct-AWQ \
  /app/data/train/train.jsonl \
  /tmp/models
```

## 5. Run Evaluation

### Via API
```bash
curl -X POST http://localhost:8007/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "model_version": "v1.0-finetuned",
    "eval_dataset": "/app/data/eval/eval.jsonl",
    "metrics": ["exact_match", "f1", "bleu", "hallucination_rate"],
    "source_documents": "/app/data/eval/sources.json"
  }'
```

Response:
```json
{
  "model_version": "v1.0-finetuned",
  "results": {
    "qa_metrics": {
      "exact_match": 0.72,
      "f1": 0.84,
      "bleu": 0.45
    },
    "quality_metrics": {
      "relevance": 4.2,
      "correctness": 4.1,
      "completeness": 4.0,
      "clarity": 4.3,
      "overall": 4.15
    },
    "hallucination_metrics": {
      "average_hallucination_rate": 0.08,
      "max_hallucination_rate": 0.25
    }
  },
  "eval_samples": 500,
  "evaluated_at": "2026-02-24T12:00:00Z"
}
```

### Via Script
```bash
./scripts/run_eval.sh \
  /app/data/eval/eval.jsonl \
  /app/data/eval/sources.json
```

This generates reports at `/tmp/eval_reports/`:
- `results.json` - Machine-readable metrics
- `report.md` - Human-readable summary
- `report.html` - Interactive visualization

## 6. Continuous Learning

### Collect User Feedback
```python
from app.continuous_learning.feedback_collector import FeedbackCollector

collector = FeedbackCollector()

# Record feedback
feedback = collector.collect_feedback(
    user_query="What is the Ministry of Culture?",
    model_response="The Ministry is responsible for culture.",
    rating=2,
    feedback_type="correction",
    corrected_response="The Ministry of Culture promotes Indian heritage and traditions.",
    metadata={"user_id": "user_123", "session_id": "sess_456"}
)
```

### Collect Batch Feedback
```python
feedback_records = [
    {
        "user_query": "Question 1",
        "model_response": "Response 1",
        "rating": 2,
        "corrected_response": "Better response 1"
    },
    # More feedback...
]

count = collector.collect_batch_feedback(feedback_records)
print(f"Collected {count} feedback records")
```

### Aggregate and Use for Retraining
```python
# Aggregate feedback
stats = collector.aggregate_feedback(min_rating=3)
print(f"Average rating: {stats['average_rating']:.2f}")
print(f"Negative samples: {len(stats['negative_samples'])}")

# Generate retraining dataset
dataset_file = collector.generate_retraining_dataset(
    min_rating=3,
    output_file="/app/data/feedback_retraining.jsonl"
)

# Use this dataset to trigger retraining
```

### Monitor Data Drift
```python
from app.continuous_learning.data_drift_detector import DataDriftDetector

detector = DataDriftDetector()

# Load new documents
new_documents = [...]  # New Ministry content

# Compute baseline (from original training docs)
baseline = detector.compute_baseline_statistics(training_documents)

# Check for drift
result = detector.detect_drift(
    current_documents=new_documents,
    baseline_stats=baseline,
    drift_threshold=0.25
)

if result["drift_detected"]:
    print(f"Data drift detected! Score: {result['drift_score']:.2f}")
    print(f"New sites: {result['new_sites']}")

    # Could trigger retraining here
```

### Schedule Periodic Retraining
```python
from app.continuous_learning.retrain_scheduler import RetrainScheduler

scheduler = RetrainScheduler()

# Schedule a job
scheduler.schedule_retraining_job(
    job_name="ministry_weekly_retrain",
    base_model="meta-llama/Llama-3.1-8B-Instruct-AWQ",
    dataset_path="s3://models/training_data/combined_dataset.jsonl",
    schedule_interval_hours=168,  # 1 week
    hyperparameters={
        "lora_rank": 16,
        "learning_rate": 0.0002,
        "epochs": 3,
        "batch_size": 4
    }
)

# Check status
status = scheduler.get_schedule_status()
print(f"Due jobs: {status['due_jobs_count']}")
```

## 7. Monitoring

### Prometheus Metrics
```bash
curl http://localhost:8007/metrics
```

Includes:
- HTTP request counts and latencies
- Training job counts and durations
- Evaluation metrics
- GPU memory utilization
- Cache hit rates

### Logs
```bash
# View logs (JSON structured)
docker logs model-training | jq '.'

# Filter by level
docker logs model-training | jq 'select(.level=="ERROR")'

# Filter by service
docker logs model-training | jq 'select(.service=="lora_trainer")'
```

## 8. Troubleshooting

### GPU Not Available
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Check CUDA version
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi
```

### Out of Memory
- Reduce `TRAINING_BATCH_SIZE` (default 4)
- Enable gradient checkpointing (enabled by default)
- Reduce `TRAINING_MAX_SEQ_LENGTH` (default 2048)
- Use smaller model (e.g., Llama 3.1 7B instead of 8B)

### Dataset Format Issues
```bash
# Validate dataset
python -c "
from app.training.data_preparer import DataPreparer
preparer = DataPreparer()
if preparer.validate_dataset('path/to/dataset.jsonl'):
    print('Dataset is valid!')
else:
    print('Dataset has errors!')
"
```

### Model Loading Failures
- Ensure HuggingFace token is set: `huggingface-cli login`
- Check internet connectivity for model download
- Verify CUDA/cuDNN compatibility

## 9. Example Workflow

```bash
# 1. Prepare data
./scripts/prepare_training_data.sh

# 2. Start training
JOB_ID=$(curl -s -X POST http://localhost:8007/finetune/start \
  -H "Content-Type: application/json" \
  -d '{...}' | jq -r '.job_id')

# 3. Monitor progress
watch -n 5 "curl -s http://localhost:8007/finetune/status?job_id=$JOB_ID | jq '.'"

# 4. Wait for completion
while [ "$(curl -s http://localhost:8007/finetune/status?job_id=$JOB_ID | jq -r '.status')" != "completed" ]; do
  sleep 10
done

# 5. Run evaluation
curl -X POST http://localhost:8007/evaluate \
  -H "Content-Type: application/json" \
  -d '{...}'

# 6. Review reports
cat /tmp/eval_reports/report.md
```

## 10. Documentation

- **Full Architecture**: `README.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **API Specification**: Shared Contracts (§8.7)
- **Configuration**: `app/config.py`
- **Source Code**: Well-commented modules in `app/`

---

**Need Help?**
- Check logs: `docker logs model-training`
- Review metrics: `curl http://localhost:8007/metrics`
- Health status: `curl http://localhost:8007/health`
- Implementation plan: `Implementation_Plan/Stream_14_Model_Training.md`
