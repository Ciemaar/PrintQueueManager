#!/bin/bash
sed -i 's/from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleIntervalSpec, ScheduleSpec/from temporalio.client import (\\n    Client,\\n    Schedule,\\n    ScheduleActionStartWorkflow,\\n    ScheduleIntervalSpec,\\n    ScheduleSpec,\\n)/g' src/worker/main.py

sed -i 's/"""Setup periodic schedules if they don'\''t already exist."""/"""Set up periodic schedules if they do not already exist."""/g' src/worker/main.py

sed -i 's/class SyncMakerworldWorkflow:/class SyncMakerworldWorkflow:\\n    """Workflow to sync Makerworld."""/g' src/worker/temporal_workflows.py
sed -i 's/class SyncPrintablesWorkflow:/class SyncPrintablesWorkflow:\\n    """Workflow to sync Printables."""/g' src/worker/temporal_workflows.py
sed -i 's/class SyncThingiverseWorkflow:/class SyncThingiverseWorkflow:\\n    """Workflow to sync Thingiverse."""/g' src/worker/temporal_workflows.py
sed -i 's/class SyncCults3dWorkflow:/class SyncCults3dWorkflow:\\n    """Workflow to sync Cults3d."""/g' src/worker/temporal_workflows.py
sed -i 's/class SyncMinihoarderWorkflow:/class SyncMinihoarderWorkflow:\\n    """Workflow to sync Minihoarder."""/g' src/worker/temporal_workflows.py
sed -i 's/class SyncLocalWorkflow:/class SyncLocalWorkflow:\\n    """Workflow to sync Local."""/g' src/worker/temporal_workflows.py

sed -i 's/async def run(self) -> List\[dict\[str, Any\]\]:/async def run(self) -> List[dict[str, Any]]:\\n        """Run the workflow."""/g' src/worker/temporal_workflows.py

sed -i 's/def mock_temporal_client():/def mock_temporal_client():\\n    """Mock the Temporal client."""/g' tests/unit/test_main_sync.py
sed -i 's/    """Ensure that the local platform triggers the Temporal workflow and returns a success message."""/    """Ensure that the local platform triggers the Temporal workflow."""/g' tests/unit/test_main_sync.py
