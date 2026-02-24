"""APScheduler-based cron scheduler for periodic re-scraping."""

import structlog
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = structlog.get_logger()


class CronScheduler:
    """Periodic scraping scheduler using APScheduler."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.scheduled_jobs: Dict[str, Any] = {}

    async def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("cron_scheduler_started")

    async def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("cron_scheduler_stopped")

    async def schedule_periodic_scrape(
        self,
        target_id: str,
        target_url: str,
        spider_type: str,
        interval_hours: int,
        job_callback=None,
    ) -> bool:
        """Schedule periodic scraping for a target.

        Args:
            target_id: Target ID
            target_url: URL to scrape
            spider_type: Type of spider
            interval_hours: Interval in hours
            job_callback: Callback function for job execution

        Returns:
            True if scheduled successfully
        """
        try:
            job_id = f"scrape_{target_id}"

            # Convert hours to cron expression
            # For simplicity, schedule every N hours starting at midnight
            cron_trigger = CronTrigger(
                hour=f"*/{max(1, interval_hours)}",
                minute="0",
            )

            # Schedule the job
            job = self.scheduler.add_job(
                job_callback or self._default_scrape_job,
                trigger=cron_trigger,
                id=job_id,
                args=[target_url, spider_type, target_id],
                name=f"Scrape {target_url}",
                replace_existing=True,
            )

            self.scheduled_jobs[target_id] = {
                "job_id": job_id,
                "target_url": target_url,
                "spider_type": spider_type,
                "interval_hours": interval_hours,
                "next_run_time": job.next_run_time,
                "created_at": datetime.utcnow(),
            }

            logger.info(
                "scrape_job_scheduled",
                target_id=target_id,
                target_url=target_url,
                interval_hours=interval_hours,
                next_run=job.next_run_time,
            )

            return True

        except Exception as e:
            logger.error(
                "schedule_scrape_error",
                target_id=target_id,
                error=str(e),
                exc_info=True,
            )
            return False

    async def unschedule_scrape(self, target_id: str) -> bool:
        """Remove scheduled scraping for a target.

        Args:
            target_id: Target ID

        Returns:
            True if unscheduled successfully
        """
        try:
            job_id = f"scrape_{target_id}"

            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                del self.scheduled_jobs[target_id]

                logger.info(
                    "scrape_job_unscheduled",
                    target_id=target_id,
                )

                return True

            return False

        except Exception as e:
            logger.error(
                "unschedule_scrape_error",
                target_id=target_id,
                error=str(e),
            )
            return False

    async def reschedule_scrape(
        self,
        target_id: str,
        new_interval_hours: int,
    ) -> bool:
        """Update scraping interval for a target.

        Args:
            target_id: Target ID
            new_interval_hours: New interval in hours

        Returns:
            True if rescheduled successfully
        """
        try:
            job_id = f"scrape_{target_id}"

            if target_id not in self.scheduled_jobs:
                return False

            job_info = self.scheduled_jobs[target_id]

            # Unschedule and reschedule with new interval
            await self.unschedule_scrape(target_id)
            await self.schedule_periodic_scrape(
                target_id,
                job_info["target_url"],
                job_info["spider_type"],
                new_interval_hours,
            )

            logger.info(
                "scrape_job_rescheduled",
                target_id=target_id,
                new_interval_hours=new_interval_hours,
            )

            return True

        except Exception as e:
            logger.error(
                "reschedule_scrape_error",
                target_id=target_id,
                error=str(e),
            )
            return False

    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs.

        Returns:
            Dictionary of scheduled jobs
        """
        jobs = {}

        for job in self.scheduler.get_jobs():
            job_id = job.id

            if job_id.startswith("scrape_"):
                target_id = job_id.replace("scrape_", "")
                jobs[target_id] = {
                    "job_id": job_id,
                    "next_run_time": job.next_run_time,
                    "last_run_time": job.last_run_time,
                    "trigger": str(job.trigger),
                }

        return jobs

    async def _default_scrape_job(
        self,
        target_url: str,
        spider_type: str,
        target_id: str,
    ):
        """Default scraping job callback.

        Args:
            target_url: URL to scrape
            spider_type: Spider type
            target_id: Target ID
        """
        logger.info(
            "scheduled_scrape_job_started",
            target_id=target_id,
            target_url=target_url,
            spider_type=spider_type,
        )

        # This would trigger the actual scraping job
        # In production, this would call the scraping pipeline
