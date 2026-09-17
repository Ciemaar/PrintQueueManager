"""RQ Scheduler configuration to register periodic tasks based on config."""

import logging
from datetime import datetime, timezone

from rq_scheduler import Scheduler

from src.app.config import settings
from src.app.logging_config import setup_logging
from src.worker.rq_worker import (
    get_redis_connection,
    sync_cults3d,
    sync_makerworld,
    sync_minihoarder,
    sync_printables,
    sync_thingiverse,
)

setup_logging()
logger = logging.getLogger(__name__)


def setup_periodic_tasks() -> Scheduler:
    """Register all platform synchronization tasks to run automatically based on config."""
    redis_conn = get_redis_connection()
    scheduler = Scheduler(connection=redis_conn)

    # Clear existing jobs if we restart the scheduler
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    # Note: the scheduler needs the interval in seconds. settings are float seconds.
    now = datetime.now(timezone.utc)

    logger.info("Registering sync_makerworld periodic task...")
    scheduler.schedule(
        scheduled_time=now,  # run immediately
        func=sync_makerworld,
        interval=settings.makerworld_sync_interval,
        repeat=None,  # forever
    )

    logger.info("Registering sync_printables periodic task...")
    scheduler.schedule(
        scheduled_time=now,
        func=sync_printables,
        interval=settings.printables_sync_interval,
        repeat=None,
    )

    logger.info("Registering sync_thingiverse periodic task...")
    scheduler.schedule(
        scheduled_time=now,
        func=sync_thingiverse,
        interval=settings.thingiverse_sync_interval,
        repeat=None,
    )

    logger.info("Registering sync_cults3d periodic task...")
    scheduler.schedule(
        scheduled_time=now, func=sync_cults3d, interval=settings.cults3d_sync_interval, repeat=None
    )

    logger.info("Registering sync_minihoarder periodic task...")
    scheduler.schedule(
        scheduled_time=now,
        func=sync_minihoarder,
        interval=settings.minihoarder_sync_interval,
        repeat=None,
    )

    return scheduler


if __name__ == "__main__":
    setup_periodic_tasks()
    logger.info("Scheduler configured.")
