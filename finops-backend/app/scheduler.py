"""
Background scheduler for periodic data refresh.
Uses APScheduler with SQLite job store for persistence.
"""
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

logger = logging.getLogger(__name__)

# Scheduler instance
scheduler: AsyncIOScheduler = None


def init_scheduler(database_url: str = "sqlite:///./finops_jobs.db"):
    """Initialize the background scheduler."""
    global scheduler
    
    jobstores = {
        'default': SQLAlchemyJobStore(url=database_url)
    }
    
    executors = {
        'default': AsyncIOExecutor()
    }
    
    job_defaults = {
        'coalesce': True,  # Combine missed runs into one
        'max_instances': 1,  # Only one instance of each job at a time
        'misfire_grace_time': 300  # 5 min grace period for missed jobs
    }
    
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )
    
    return scheduler


def get_scheduler() -> AsyncIOScheduler:
    """Get the scheduler instance."""
    global scheduler
    if scheduler is None:
        scheduler = init_scheduler()
    return scheduler


async def start_scheduler():
    """Start the scheduler and register jobs."""
    sched = get_scheduler()
    
    # Import jobs here to avoid circular imports
    from app.jobs.refresh_jobs import (
        refresh_daily_costs,
        refresh_recommendations,
        refresh_budgets,
        detect_anomalies
    )
    
    # Clear existing jobs to avoid duplicates on restart
    sched.remove_all_jobs()
    
    # Schedule jobs
    sched.add_job(
        refresh_daily_costs,
        'interval',
        hours=1,
        id='refresh_daily_costs',
        name='Refresh Daily Costs',
        next_run_time=datetime.utcnow()  # Run immediately on startup
    )
    
    sched.add_job(
        refresh_recommendations,
        'interval',
        hours=6,  # RI recommendations don't change frequently
        id='refresh_recommendations',
        name='Refresh RI/SP Recommendations',
        next_run_time=datetime.utcnow()
    )
    
    sched.add_job(
        refresh_budgets,
        'interval',
        hours=1,
        id='refresh_budgets',
        name='Refresh Azure Budgets',
        next_run_time=datetime.utcnow()
    )
    
    sched.add_job(
        detect_anomalies,
        'interval',
        hours=1,
        id='detect_anomalies',
        name='Detect Cost Anomalies',
        next_run_time=datetime.utcnow()
    )
    
    sched.start()
    logger.info("Background scheduler started with 4 jobs")


async def stop_scheduler():
    """Gracefully stop the scheduler."""
    sched = get_scheduler()
    if sched.running:
        sched.shutdown(wait=True)
        logger.info("Scheduler stopped")
