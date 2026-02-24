"""Periodic retraining scheduler."""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from app.utils.logging_config import setup_json_logging


logger = setup_json_logging("retrain_scheduler")


class RetrainScheduler:
    """Schedule and manage periodic retraining jobs."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize retraining scheduler.

        Args:
            config_file: Optional configuration file path
        """
        self.config_file = config_file or "/app/config/retrain_schedule.json"
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_history: List[Dict[str, Any]] = []
        self._load_config()

    def _load_config(self):
        """Load scheduler configuration."""
        config_path = Path(self.config_file)

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.scheduled_jobs = config.get("scheduled_jobs", {})
                    self.job_history = config.get("job_history", [])

                logger.info(
                    "Loaded retrain schedule configuration",
                    extra={"jobs": len(self.scheduled_jobs)},
                )
            except Exception as e:
                logger.warning(
                    "Failed to load schedule configuration",
                    extra={"file": self.config_file, "error": str(e)},
                )
        else:
            logger.info("No existing schedule configuration found")

    def schedule_retraining_job(
        self,
        job_name: str,
        base_model: str,
        dataset_path: str,
        schedule_interval_hours: int = 168,  # 1 week default
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Schedule a retraining job.

        Args:
            job_name: Name of the job
            base_model: Base model to fine-tune
            dataset_path: Path to training dataset
            schedule_interval_hours: Interval in hours
            hyperparameters: Optional hyperparameters

        Returns:
            Job schedule configuration
        """
        job_config = {
            "job_name": job_name,
            "base_model": base_model,
            "dataset_path": dataset_path,
            "schedule_interval_hours": schedule_interval_hours,
            "hyperparameters": hyperparameters or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "last_run": None,
            "next_run": datetime.utcnow().isoformat() + "Z",
            "enabled": True,
            "run_count": 0,
        }

        self.scheduled_jobs[job_name] = job_config

        logger.info(
            "Scheduled retraining job",
            extra={
                "job_name": job_name,
                "interval_hours": schedule_interval_hours,
                "base_model": base_model,
            },
        )

        self._save_config()

        return job_config

    def get_due_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs that are due to run.

        Returns:
            List of due jobs
        """
        due_jobs = []
        now = datetime.utcnow()

        for job_name, job_config in self.scheduled_jobs.items():
            if not job_config.get("enabled", True):
                continue

            next_run_str = job_config.get("next_run")
            if next_run_str:
                next_run = datetime.fromisoformat(next_run_str.replace("Z", "+00:00"))

                if now >= next_run:
                    due_jobs.append(job_config)
                    logger.info(
                        "Job is due for execution",
                        extra={"job_name": job_name},
                    )

        return due_jobs

    def mark_job_completed(
        self,
        job_name: str,
        status: str = "completed",
        output_path: Optional[str] = None,
    ):
        """Mark a retraining job as completed.

        Args:
            job_name: Name of the job
            status: Job status (completed, failed)
            output_path: Path to output model
        """
        if job_name not in self.scheduled_jobs:
            logger.warning(
                "Job not found in schedule",
                extra={"job_name": job_name},
            )
            return

        job_config = self.scheduled_jobs[job_name]

        # Update job record
        job_config["last_run"] = datetime.utcnow().isoformat() + "Z"
        job_config["run_count"] = job_config.get("run_count", 0) + 1

        # Calculate next run
        interval_hours = job_config.get("schedule_interval_hours", 168)
        next_run = datetime.utcnow() + timedelta(hours=interval_hours)
        job_config["next_run"] = next_run.isoformat() + "Z"

        # Add to history
        history_entry = {
            "job_name": job_name,
            "status": status,
            "completed_at": datetime.utcnow().isoformat() + "Z",
            "output_path": output_path,
        }
        self.job_history.append(history_entry)

        logger.info(
            "Job marked as completed",
            extra={
                "job_name": job_name,
                "status": status,
                "next_run": job_config["next_run"],
            },
        )

        self._save_config()

    def get_job_history(
        self,
        job_name: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get job execution history.

        Args:
            job_name: Optional filter by job name
            limit: Maximum history entries to return

        Returns:
            Job history
        """
        history = self.job_history

        if job_name:
            history = [h for h in history if h.get("job_name") == job_name]

        # Return most recent entries
        return history[-limit:]

    def get_schedule_status(self) -> Dict[str, Any]:
        """Get overall scheduler status.

        Returns:
            Scheduler status
        """
        due_jobs = self.get_due_jobs()
        total_jobs = len(self.scheduled_jobs)
        enabled_jobs = sum(
            1 for j in self.scheduled_jobs.values()
            if j.get("enabled", True)
        )

        total_runs = sum(
            j.get("run_count", 0) for j in self.scheduled_jobs.values()
        )

        recent_history = self.job_history[-5:] if self.job_history else []

        return {
            "total_jobs": total_jobs,
            "enabled_jobs": enabled_jobs,
            "due_jobs_count": len(due_jobs),
            "due_jobs": due_jobs,
            "total_runs": total_runs,
            "recent_history": recent_history,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def disable_job(self, job_name: str):
        """Disable a scheduled job.

        Args:
            job_name: Name of the job
        """
        if job_name in self.scheduled_jobs:
            self.scheduled_jobs[job_name]["enabled"] = False
            logger.info("Job disabled", extra={"job_name": job_name})
            self._save_config()

    def enable_job(self, job_name: str):
        """Enable a scheduled job.

        Args:
            job_name: Name of the job
        """
        if job_name in self.scheduled_jobs:
            self.scheduled_jobs[job_name]["enabled"] = True
            logger.info("Job enabled", extra={"job_name": job_name})
            self._save_config()

    def update_job_schedule(
        self,
        job_name: str,
        schedule_interval_hours: int,
    ):
        """Update job schedule interval.

        Args:
            job_name: Name of the job
            schedule_interval_hours: New interval in hours
        """
        if job_name in self.scheduled_jobs:
            self.scheduled_jobs[job_name]["schedule_interval_hours"] = schedule_interval_hours

            # Recalculate next run
            last_run = self.scheduled_jobs[job_name].get("last_run")
            if last_run:
                last_run_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
                next_run = last_run_dt + timedelta(hours=schedule_interval_hours)
            else:
                next_run = datetime.utcnow() + timedelta(hours=schedule_interval_hours)

            self.scheduled_jobs[job_name]["next_run"] = next_run.isoformat() + "Z"

            logger.info(
                "Job schedule updated",
                extra={
                    "job_name": job_name,
                    "interval_hours": schedule_interval_hours,
                    "next_run": self.scheduled_jobs[job_name]["next_run"],
                },
            )

            self._save_config()

    def _save_config(self):
        """Save scheduler configuration to file."""
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            config = {
                "scheduled_jobs": self.scheduled_jobs,
                "job_history": self.job_history,
                "last_updated": datetime.utcnow().isoformat() + "Z",
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.debug("Saved scheduler configuration", extra={"file": self.config_file})

        except Exception as e:
            logger.error(
                "Failed to save scheduler configuration",
                extra={"file": self.config_file, "error": str(e)},
                exc_info=True,
            )

    async def start_scheduler(self, poll_interval_seconds: int = 3600):
        """Start the scheduler loop.

        Args:
            poll_interval_seconds: Polling interval in seconds
        """
        logger.info(
            "Starting retraining scheduler",
            extra={"poll_interval_seconds": poll_interval_seconds},
        )

        try:
            while True:
                # Check for due jobs
                due_jobs = self.get_due_jobs()

                if due_jobs:
                    logger.info(
                        "Found due jobs",
                        extra={"count": len(due_jobs)},
                    )

                    for job in due_jobs:
                        logger.info(
                            "Would execute job",
                            extra={"job_name": job.get("job_name")},
                        )
                        # In production, trigger actual training job here

                # Wait for next poll
                await asyncio.sleep(poll_interval_seconds)

        except Exception as e:
            logger.error(
                "Scheduler error",
                extra={"error": str(e)},
                exc_info=True,
            )
