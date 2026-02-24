"""Fine-tuning API endpoints."""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field

from app.config import get_config
from app.training.data_preparer import DataPreparer
from app.training.lora_trainer import LoRATrainer
from app.training.training_config import get_default_training_config
from app.utils.logging_config import setup_json_logging
from app.utils.metrics import record_training_job


logger = setup_json_logging("finetune")
config = get_config()
router = APIRouter()

# In-memory job tracking (in production, use Redis or database)
_training_jobs: Dict[str, Dict[str, Any]] = {}


class FinetuneStartRequest(BaseModel):
    """Request to start fine-tuning."""

    base_model: str = Field(
        ...,
        description="Base model name (e.g., meta-llama/Llama-3.1-8B-Instruct-AWQ)"
    )
    dataset_path: str = Field(
        ...,
        description="Path to training dataset (JSONL format)"
    )
    hyperparameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom hyperparameters (lora_rank, learning_rate, epochs, etc.)"
    )


class FinetuneStartResponse(BaseModel):
    """Response from starting fine-tuning."""

    job_id: str
    status: str
    estimated_duration_minutes: int
    created_at: str


class FinetuneStatusResponse(BaseModel):
    """Response with fine-tuning status."""

    job_id: str
    status: str  # started, running, completed, failed
    progress: float  # 0.0-1.0
    training_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    steps_completed: int
    total_steps: int
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


@router.post("/start", response_model=FinetuneStartResponse)
async def start_finetune(
    request: FinetuneStartRequest,
    background_tasks: BackgroundTasks,
    x_request_id: Optional[str] = Header(None),
) -> FinetuneStartResponse:
    """Start a fine-tuning job.

    Args:
        request: Fine-tuning start request
        background_tasks: Background task runner
        x_request_id: Request ID header

    Returns:
        Fine-tuning job response
    """
    job_id = str(uuid.uuid4())

    logger.info(
        "Starting fine-tuning job",
        extra={
            "job_id": job_id,
            "base_model": request.base_model,
            "dataset_path": request.dataset_path,
            "request_id": x_request_id,
        },
    )

    # Check concurrent job limit
    active_jobs = sum(
        1 for j in _training_jobs.values()
        if j.get("status") in ["started", "running"]
    )

    if active_jobs >= config.MAX_CONCURRENT_TRAINING_JOBS:
        logger.warning(
            "Max concurrent jobs reached",
            extra={"active_jobs": active_jobs, "request_id": x_request_id},
        )
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Maximum concurrent training jobs ({config.MAX_CONCURRENT_TRAINING_JOBS}) reached",
                    "request_id": x_request_id,
                }
            },
        )

    # Initialize job tracking
    _training_jobs[job_id] = {
        "status": "started",
        "base_model": request.base_model,
        "dataset_path": request.dataset_path,
        "hyperparameters": request.hyperparameters or {},
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "progress": 0.0,
        "steps_completed": 0,
        "total_steps": 0,
        "training_loss": None,
        "eval_loss": None,
        "error_message": None,
    }

    # Schedule background training
    background_tasks.add_task(
        _run_finetune_job,
        job_id,
        request.base_model,
        request.dataset_path,
        request.hyperparameters,
    )

    record_training_job(request.base_model, job_id, "started")

    return FinetuneStartResponse(
        job_id=job_id,
        status="started",
        estimated_duration_minutes=120,
        created_at=_training_jobs[job_id]["created_at"],
    )


@router.get("/status", response_model=FinetuneStatusResponse)
async def get_finetune_status(
    job_id: str,
    x_request_id: Optional[str] = Header(None),
) -> FinetuneStatusResponse:
    """Get fine-tuning job status.

    Args:
        job_id: Job ID
        x_request_id: Request ID header

    Returns:
        Fine-tuning status response
    """
    if job_id not in _training_jobs:
        logger.warning(
            "Job not found",
            extra={"job_id": job_id, "request_id": x_request_id},
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "request_id": x_request_id,
                }
            },
        )

    job = _training_jobs[job_id]

    # Calculate elapsed time
    created_at = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
    elapsed = (updated_at - created_at).total_seconds()

    # Calculate estimated remaining time
    estimated_remaining = None
    if job["progress"] > 0 and job["status"] == "running":
        estimated_remaining = (elapsed / job["progress"]) * (1 - job["progress"])

    return FinetuneStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        training_loss=job.get("training_loss"),
        eval_loss=job.get("eval_loss"),
        steps_completed=job.get("steps_completed", 0),
        total_steps=job.get("total_steps", 0),
        elapsed_seconds=elapsed,
        estimated_remaining_seconds=estimated_remaining,
        error_message=job.get("error_message"),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


async def _run_finetune_job(
    job_id: str,
    base_model: str,
    dataset_path: str,
    hyperparameters: Optional[Dict[str, Any]] = None,
):
    """Run fine-tuning job in background.

    Args:
        job_id: Job ID
        base_model: Base model name
        dataset_path: Dataset path
        hyperparameters: Custom hyperparameters
    """
    try:
        _training_jobs[job_id]["status"] = "running"
        _training_jobs[job_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"

        logger.info("Fine-tuning job running", extra={"job_id": job_id})

        # Create training config
        training_config = get_default_training_config(
            model_name=base_model,
            output_dir=f"/tmp/model_outputs/{job_id}",
            train_dataset_path=dataset_path,
        )

        # Override with custom hyperparameters if provided
        if hyperparameters:
            if "lora_rank" in hyperparameters:
                training_config.lora.lora_r = hyperparameters["lora_rank"]
            if "learning_rate" in hyperparameters:
                training_config.training_args.learning_rate = hyperparameters["learning_rate"]
            if "epochs" in hyperparameters:
                training_config.training_args.num_train_epochs = hyperparameters["epochs"]
            if "batch_size" in hyperparameters:
                training_config.training_args.per_device_train_batch_size = hyperparameters["batch_size"]

        # Initialize trainer
        trainer = LoRATrainer(training_config)

        # Prepare model
        logger.info("Loading model and tokenizer", extra={"job_id": job_id})
        trainer.prepare_model_and_tokenizer()

        # Load and preprocess data
        logger.info("Loading dataset", extra={"job_id": job_id})
        dataset = trainer.load_dataset(dataset_path)

        logger.info("Preprocessing dataset", extra={"job_id": job_id})
        train_dataset = trainer.preprocess_dataset(
            dataset,
            max_seq_length=training_config.data.max_seq_length,
        )

        _training_jobs[job_id]["total_steps"] = (
            len(train_dataset) // training_config.training_args.per_device_train_batch_size
        ) * training_config.training_args.num_train_epochs

        # Run training
        logger.info("Starting training", extra={"job_id": job_id})
        result = await asyncio.to_thread(
            trainer.train,
            train_dataset,
            None,
            job_id,
        )

        if result["status"] == "completed":
            # Save model
            output_dir = trainer.save_model(f"/tmp/models/{job_id}")

            _training_jobs[job_id]["status"] = "completed"
            _training_jobs[job_id]["output_path"] = output_dir
            _training_jobs[job_id]["training_loss"] = result.get("training_loss")
            _training_jobs[job_id]["eval_loss"] = result.get("eval_loss")
            _training_jobs[job_id]["progress"] = 1.0
            _training_jobs[job_id]["steps_completed"] = _training_jobs[job_id]["total_steps"]

            logger.info(
                "Fine-tuning job completed",
                extra={
                    "job_id": job_id,
                    "duration_seconds": result.get("duration_seconds"),
                    "output_path": output_dir,
                },
            )

            record_training_job(base_model, job_id, "completed")
        else:
            _training_jobs[job_id]["status"] = "failed"
            _training_jobs[job_id]["error_message"] = result.get("error", "Unknown error")

            logger.error(
                "Fine-tuning job failed",
                extra={
                    "job_id": job_id,
                    "error": result.get("error"),
                },
            )

            record_training_job(base_model, job_id, "failed")

    except Exception as e:
        _training_jobs[job_id]["status"] = "failed"
        _training_jobs[job_id]["error_message"] = str(e)

        logger.error(
            "Fine-tuning job exception",
            extra={"job_id": job_id, "error": str(e)},
            exc_info=True,
        )

        record_training_job(base_model, job_id, "failed")

    finally:
        _training_jobs[job_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
