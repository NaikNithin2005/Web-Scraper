"""
Scheduler Module
Handles automated scraping jobs with cron-based scheduling.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import time


class ScrapingScheduler:
    """
    Scheduler for automated scraping jobs.
    Supports hourly, daily, monthly, and custom cron schedules.
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs = {}  # job_id -> job_info
        self.job_callbacks = {}  # job_id -> callback function
        logger.info("Scraping scheduler initialized")
    
    def add_job(
        self,
        job_id: str,
        callback: Callable,
        schedule_type: str = "interval",
        interval_hours: Optional[int] = None,
        interval_days: Optional[int] = None,
        cron_expression: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> str:
        """
        Add a scheduled scraping job.
        
        Args:
            job_id: Unique job identifier
            callback: Function to call when job runs
            schedule_type: "interval", "cron", or "date"
            interval_hours: Hours between runs (for interval)
            interval_days: Days between runs (for interval)
            cron_expression: Cron expression (e.g., "0 0 * * *" for daily)
            start_date: When to start the job
            end_date: When to end the job
            **kwargs: Additional arguments for callback
            
        Returns:
            Job ID
        """
        trigger = None
        
        if schedule_type == "interval":
            if interval_hours:
                trigger = IntervalTrigger(hours=interval_hours)
            elif interval_days:
                trigger = IntervalTrigger(days=interval_days)
            else:
                trigger = IntervalTrigger(hours=1)  # Default: hourly
        
        elif schedule_type == "cron":
            if cron_expression:
                # Parse cron expression: minute hour day month day_of_week
                parts = cron_expression.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4]
                    )
                else:
                    raise ValueError("Invalid cron expression. Use format: 'minute hour day month day_of_week'")
            else:
                # Default: daily at midnight
                trigger = CronTrigger(hour=0, minute=0)
        
        elif schedule_type == "date":
            if start_date:
                trigger = DateTrigger(run_date=start_date)
            else:
                trigger = DateTrigger(run_date=datetime.now() + timedelta(seconds=5))
        
        else:
            raise ValueError(f"Unknown schedule_type: {schedule_type}")
        
        # Create wrapper function to log and handle errors
        def job_wrapper():
            try:
                logger.info(f"Running scheduled job: {job_id}")
                result = callback(**kwargs)
                logger.info(f"Job {job_id} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                raise
        
        # Schedule the job
        scheduled_job = self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id=job_id,
            replace_existing=True
        )
        
        self.jobs[job_id] = {
            "id": job_id,
            "schedule_type": schedule_type,
            "trigger": str(trigger),
            "created_at": datetime.now(),
            "next_run": scheduled_job.next_run_time
        }
        
        self.job_callbacks[job_id] = callback
        
        logger.info(f"Scheduled job {job_id} with trigger: {trigger}")
        return job_id
    
    def add_daily_job(
        self,
        job_id: str,
        callback: Callable,
        hour: int = 0,
        minute: int = 0,
        **kwargs
    ) -> str:
        """Add a daily job."""
        return self.add_job(
            job_id,
            callback,
            schedule_type="cron",
            cron_expression=f"{minute} {hour} * * *",
            **kwargs
        )
    
    def add_hourly_job(
        self,
        job_id: str,
        callback: Callable,
        minute: int = 0,
        **kwargs
    ) -> str:
        """Add an hourly job."""
        return self.add_job(
            job_id,
            callback,
            schedule_type="cron",
            cron_expression=f"{minute} * * * *",
            **kwargs
        )
    
    def add_monthly_job(
        self,
        job_id: str,
        callback: Callable,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        **kwargs
    ) -> str:
        """Add a monthly job."""
        return self.add_job(
            job_id,
            callback,
            schedule_type="cron",
            cron_expression=f"{minute} {hour} {day} * *",
            **kwargs
        )
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            if job_id in self.job_callbacks:
                del self.job_callbacks[job_id]
            logger.info(f"Removed job: {job_id}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job information."""
        if job_id in self.jobs:
            job_info = self.jobs[job_id].copy()
            try:
                scheduled_job = self.scheduler.get_job(job_id)
                if scheduled_job:
                    job_info["next_run"] = scheduled_job.next_run_time.isoformat() if scheduled_job.next_run_time else None
                    job_info["previous_run"] = scheduled_job.trigger.get_next_fire_time(None, datetime.now()).isoformat() if hasattr(scheduled_job.trigger, 'get_next_fire_time') else None
            except Exception as e:
                logger.debug(f"Error getting job details: {e}")
            return job_info
        return None
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        return list(self.jobs.values())
    
    def pause_job(self, job_id: str):
        """Pause a job."""
        self.scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        self.scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")
    
    def run_job_now(self, job_id: str) -> Any:
        """Run a job immediately."""
        if job_id in self.job_callbacks:
            callback = self.job_callbacks[job_id]
            return callback()
        else:
            raise ValueError(f"Job {job_id} not found")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler shut down")

