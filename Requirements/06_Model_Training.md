# Model Training & Evaluation Requirements

**Source:** Requirements.pdf pages 14-15

## Fine-Tuning Requirements

### Domain Adaptation
- Base LLMs must be **fine-tuned on Ministry of Culture domain data**
- Training data sourced from the 30 ring-fenced websites (scraped content)
- Fine-tuning must improve Hindi comprehension and domain-specific accuracy
- Must support incremental fine-tuning as new content is ingested

### Training Data Generation
- **Self-instruct method** — auto-generate QA training pairs from scraped Ministry content
- Training data must be curated and validated before use
- Training dataset versioning and management

### Fine-Tuning Method
- Must be memory-efficient to fit on available GPU hardware
- QLoRA (4-bit quantized LoRA) recommended for single-GPU training
- Support fine-tuning of multiple base models (Llama, Mistral)

## Evaluation Requirements

### Benchmark Suite
The following evaluation metrics are required:

| Metric | Description |
|---|---|
| **Hindi QA Accuracy** | Exact match and F1 score on Hindi question-answering benchmarks |
| **BLEU Score** | Translation and generation quality measurement |
| **Retrieval Relevance (NDCG)** | Quality of retrieved documents/chunks for given queries |
| **Hallucination Rate** | Percentage of responses containing claims not supported by source documents |
| **Response Quality** | LLM-as-judge evaluation for overall response quality, helpfulness, accuracy |

### Evaluation Process
- Benchmark suite must run automatically after each fine-tuning cycle
- Results stored with model version for comparison
- Minimum quality thresholds must be met before model deployment
- A/B testing support for comparing model versions in production

## Continuous Learning Requirements

### Feedback Loop
- **Negative user feedback** (thumbs down, low ratings) feeds into retraining dataset
- Periodic collection and curation of feedback-based training examples
- Human review process for disputed or edge-case responses

### Data Drift Detection
- Monitor for drift between training data distribution and incoming query distribution
- Alert when drift exceeds threshold
- Trigger retraining when significant drift detected

### Retraining Pipeline
- **Periodic retraining scheduler** — configurable interval (e.g., monthly)
- Triggered automatically when:
  - New content volume crosses threshold (e.g., 1000+ new documents)
  - Data drift detected
  - Feedback-based negative examples accumulate past threshold
- Retraining must not disrupt production service (blue-green or shadow deployment)

## Model Versioning

- Each fine-tuned model tagged with:
  - Timestamp
  - Training data version
  - Evaluation scores (all benchmark metrics)
  - Training hyperparameters
  - Status (training/evaluating/deployed/archived)
- Model artifacts stored in S3 object storage
- Rollback capability to previous model version
- model_versions table in PostgreSQL for tracking
