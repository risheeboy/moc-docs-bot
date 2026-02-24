"""Evaluation API endpoints."""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from app.config import get_config
from app.evaluation.benchmark_suite import BenchmarkSuite
from app.evaluation.metrics_reporter import MetricsReporter
from app.utils.logging_config import setup_json_logging
from app.utils.metrics import record_evaluation_job


logger = setup_json_logging("evaluate")
config = get_config()
router = APIRouter()

# In-memory evaluation job tracking
_eval_jobs: Dict[str, Dict[str, Any]] = {}


class EvaluateRequest(BaseModel):
    """Request to run evaluation."""

    model_version: str = Field(
        ...,
        description="Model version to evaluate"
    )
    eval_dataset: str = Field(
        ...,
        description="Path to evaluation dataset (JSONL format)"
    )
    metrics: Optional[List[str]] = Field(
        None,
        description="Specific metrics to run (e.g., exact_match, f1, bleu, hallucination_rate)"
    )
    source_documents: Optional[str] = Field(
        None,
        description="Path to source documents for hallucination detection"
    )


class EvaluationResult(BaseModel):
    """Evaluation results."""

    model_version: str
    results: Dict[str, Any]
    eval_samples: int
    evaluated_at: str


@router.post("", response_model=EvaluationResult)
async def run_evaluation(
    request: EvaluateRequest,
    x_request_id: Optional[str] = Header(None),
) -> EvaluationResult:
    """Run model evaluation.

    Args:
        request: Evaluation request
        x_request_id: Request ID header

    Returns:
        Evaluation results
    """
    job_id = str(uuid.uuid4())

    logger.info(
        "Starting evaluation job",
        extra={
            "job_id": job_id,
            "model_version": request.model_version,
            "dataset": request.eval_dataset,
            "request_id": x_request_id,
        },
    )

    record_evaluation_job(request.model_version, "started")

    try:
        # Initialize benchmark suite
        benchmark_suite = BenchmarkSuite()

        # Load evaluation dataset
        import json
        eval_data = []
        try:
            with open(request.eval_dataset, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        eval_data.append(json.loads(line))
        except Exception as e:
            logger.error(
                "Failed to load evaluation dataset",
                extra={"path": request.eval_dataset, "error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": f"Failed to load evaluation dataset: {str(e)}",
                        "request_id": x_request_id,
                    }
                },
            )

        if not eval_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Evaluation dataset is empty",
                        "request_id": x_request_id,
                    }
                },
            )

        # Generate dummy predictions (in production, load from model)
        predictions = [
            item.get("output", "Model response for: " + item.get("input", ""))
            for item in eval_data
        ]

        # Load source documents if provided
        sources = None
        if request.source_documents:
            try:
                with open(request.source_documents, "r", encoding="utf-8") as f:
                    sources = json.load(f)
            except Exception as e:
                logger.warning(
                    "Failed to load source documents",
                    extra={"path": request.source_documents, "error": str(e)},
                )

        # Run benchmark
        logger.info("Running benchmark suite", extra={"job_id": job_id})
        results = await asyncio.to_thread(
            benchmark_suite.run_complete_benchmark,
            request.eval_dataset,
            predictions,
            sources,
        )

        # Generate reports
        reporter = MetricsReporter()

        logger.info("Generating evaluation reports", extra={"job_id": job_id})

        # Save JSON report
        json_report_path = f"/tmp/eval_reports/{job_id}/results.json"
        reporter.generate_json_report(
            results.get("metrics", {}),
            request.model_version,
            json_report_path,
        )

        # Save markdown report
        markdown_report_path = f"/tmp/eval_reports/{job_id}/report.md"
        benchmark_suite.generate_benchmark_report(
            results,
            markdown_report_path,
        )

        record_evaluation_job(request.model_version, "completed")

        logger.info(
            "Evaluation job completed",
            extra={
                "job_id": job_id,
                "model_version": request.model_version,
                "eval_samples": len(eval_data),
            },
        )

        return EvaluationResult(
            model_version=request.model_version,
            results=results.get("metrics", {}),
            eval_samples=len(eval_data),
            evaluated_at=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Evaluation failed",
            extra={
                "job_id": job_id,
                "model_version": request.model_version,
                "error": str(e),
            },
            exc_info=True,
        )

        record_evaluation_job(request.model_version, "failed")

        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Evaluation failed: {str(e)}",
                    "request_id": x_request_id,
                }
            },
        )


@router.get("/{job_id}")
async def get_evaluation_status(
    job_id: str,
    x_request_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """Get evaluation job status.

    Args:
        job_id: Job ID
        x_request_id: Request ID header

    Returns:
        Evaluation status
    """
    if job_id not in _eval_jobs:
        logger.warning(
            "Evaluation job not found",
            extra={"job_id": job_id, "request_id": x_request_id},
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Evaluation job {job_id} not found",
                    "request_id": x_request_id,
                }
            },
        )

    job = _eval_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job.get("status"),
        "model_version": job.get("model_version"),
        "progress": job.get("progress", 0.0),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }
