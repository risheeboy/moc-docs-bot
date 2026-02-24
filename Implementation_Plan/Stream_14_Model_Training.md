### STREAM 14: Model Fine-Tuning & Evaluation Pipeline (**NEW**)

**Agent Goal:** Build the model fine-tuning pipeline for domain adaptation of base LLMs on Ministry of Culture data, plus evaluation benchmarks and a continuous-learning retraining mechanism. (Requirements pages 14-15 explicitly require "Training of AI Model" on domain data, evaluation benchmarks, and continuous learning.)

**Files to create:**
```
model-training/
├── Dockerfile                       # python:3.11-slim + CUDA + transformers
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI for triggering training jobs
│   ├── config.py                    # Model IDs, training hyperparams, data paths
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── finetune.py              # POST /finetune/start, GET /finetune/status
│   │   ├── evaluate.py              # POST /evaluate (run benchmark suite)
│   │   └── health.py
│   ├── training/
│   │   ├── __init__.py
│   │   ├── data_preparer.py         # Convert scraped docs → instruction-tuning format
│   │   ├── qa_dataset_builder.py    # Generate QA pairs from Ministry content (self-instruct)
│   │   ├── lora_trainer.py          # LoRA/QLoRA fine-tuning (PEFT) on Llama 3.1 / Mistral
│   │   ├── training_config.py       # Hyperparameters, LoRA rank, learning rate schedules
│   │   └── model_merger.py          # Merge LoRA adapters back into base model
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── benchmark_suite.py       # Run benchmarks: Hindi QA accuracy, retrieval relevance
│   │   ├── hindi_qa_eval.py         # Hindi-specific QA evaluation (exact match, F1, BLEU)
│   │   ├── hallucination_detector.py# Check for hallucinated facts vs source documents
│   │   ├── response_quality.py      # LLM-as-judge evaluation for response quality
│   │   └── metrics_reporter.py      # Generate evaluation report (JSON + human-readable)
│   ├── continuous_learning/
│   │   ├── __init__.py
│   │   ├── feedback_collector.py    # Collect negative feedback for retraining dataset
│   │   ├── data_drift_detector.py   # Detect when new content diverges from training data
│   │   └── retrain_scheduler.py     # Trigger periodic retraining jobs
│   └── utils/
│       ├── __init__.py
│       └── metrics.py
├── data/
│   ├── train/                       # Training data directory
│   ├── eval/                        # Evaluation benchmark data
│   └── ministry_qa_pairs.jsonl      # Generated QA pairs from Ministry content
├── scripts/
│   ├── prepare_training_data.sh
│   ├── run_finetune.sh
│   └── run_eval.sh
└── tests/
    ├── test_data_preparer.py
    └── test_evaluation.py
```

**Key technical decisions (from Requirements page 14-15):**
- **Fine-tuning method:** QLoRA (4-bit quantized LoRA) — memory efficient, fits single GPU
- **Training data:** Auto-generated QA pairs from scraped Ministry content via self-instruct
- **Evaluation:** Hindi QA accuracy, retrieval relevance (NDCG), hallucination rate, response quality (LLM-as-judge)
- **Continuous learning:** Negative user feedback feeds into retraining dataset; periodic retraining triggered when data drift detected or new content volume crosses threshold
- **Model versioning:** Each fine-tuned model tagged with timestamp + eval score, stored in MinIO

**Requires:** GPU for training. Depends on scraped data from Stream 12 being available.

---


---

## Agent Prompt

### Agent 14: Model Fine-Tuning & Evaluation (**NEW**)
```
Build a model fine-tuning pipeline for domain adaptation:
- QLoRA (4-bit LoRA) fine-tuning of Llama 3.1 8B and Mistral NeMo on
  Ministry of Culture domain data
- Auto-generate QA training pairs from scraped content (self-instruct)
- Evaluation benchmark suite: Hindi QA accuracy (exact match, F1, BLEU),
  retrieval relevance (NDCG), hallucination rate, response quality (LLM-as-judge)
- Continuous learning: collect negative feedback → retrain dataset,
  data drift detection, periodic retraining scheduler
- Model versioning: tag fine-tuned models with eval scores, store in MinIO
- FastAPI endpoints: POST /finetune/start, GET /finetune/status, POST /evaluate
- GPU required.
```

