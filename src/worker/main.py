"""Temporal Worker initialization and execution."""

import asyncio
from datetime import timedelta

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleIntervalSpec,
    ScheduleSpec,
)
from temporalio.worker import Worker

from src.app.config import settings
from src.worker.temporal_workflows import (
    SyncCults3dWorkflow,
    SyncLocalWorkflow,
    SyncMakerworldWorkflow,
    SyncMinihoarderWorkflow,
    SyncPrintablesWorkflow,
    SyncThingiverseWorkflow,
    sync_cults3d,
    sync_local,
    sync_makerworld,
    sync_minihoarder,
    sync_printables,
    sync_thingiverse,
)


async def setup_schedules(client: Client) -> None:
    """Set up periodic schedules if they do not already exist."""
    schedules = [
        ("sync-makerworld-schedule", SyncMakerworldWorkflow, settings.makerworld_sync_interval),
        ("sync-printables-schedule", SyncPrintablesWorkflow, settings.printables_sync_interval),
        ("sync-thingiverse-schedule", SyncThingiverseWorkflow, settings.thingiverse_sync_interval),
        ("sync-cults3d-schedule", SyncCults3dWorkflow, settings.cults3d_sync_interval),
        ("sync-minihoarder-schedule", SyncMinihoarderWorkflow, settings.minihoarder_sync_interval),
    ]

    for schedule_id, workflow_cls, interval_seconds in schedules:
        try:
            await client.create_schedule(
                schedule_id,
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        workflow_cls.run,
                        id=f"{schedule_id}-workflow",
                        task_queue="sync-task-queue",
                    ),
                    spec=ScheduleSpec(
                        intervals=[ScheduleIntervalSpec(every=timedelta(seconds=interval_seconds))]
                    ),
                ),
            )
            print(f"Created schedule: {schedule_id}")
        except Exception as e:
            if "AlreadyExists" in str(e):
                print(f"Schedule already exists: {schedule_id}")
            else:
                print(f"Failed to create schedule {schedule_id}: {e}")


async def run_worker() -> None:
    """Connect to Temporal and run the worker."""
    print(f"Connecting to Temporal at {settings.temporal_target}...")
    client = await Client.connect(settings.temporal_target)

    print("Setting up schedules...")
    await setup_schedules(client)

    print("Starting Temporal Worker on task queue 'sync-task-queue'...")
    worker = Worker(
        client,
        task_queue="sync-task-queue",
        workflows=[
            SyncMakerworldWorkflow,
            SyncPrintablesWorkflow,
            SyncThingiverseWorkflow,
            SyncCults3dWorkflow,
            SyncMinihoarderWorkflow,
            SyncLocalWorkflow,
        ],
        activities=[
            sync_makerworld,
            sync_printables,
            sync_thingiverse,
            sync_cults3d,
            sync_minihoarder,
            sync_local,
        ],
    )

    await worker.run()


def main() -> None:
    """Entry point to start the Temporal worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
