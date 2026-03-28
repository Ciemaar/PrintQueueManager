import re

with open("src/worker/temporal_workflows.py", "r") as f:
    content = f.read()

content = content.replace("class SyncMakerworldWorkflow:\\n    \"\"\"Workflow to sync Makerworld.\"\"\"\n\n    @workflow.run", "class SyncMakerworldWorkflow:\n    \"\"\"Workflow to sync Makerworld.\"\"\"\n\n    @workflow.run")
content = content.replace("class SyncPrintablesWorkflow:\\n    \"\"\"Workflow to sync Printables.\"\"\"\n\n    @workflow.run", "class SyncPrintablesWorkflow:\n    \"\"\"Workflow to sync Printables.\"\"\"\n\n    @workflow.run")
content = content.replace("class SyncThingiverseWorkflow:\\n    \"\"\"Workflow to sync Thingiverse.\"\"\"\n\n    @workflow.run", "class SyncThingiverseWorkflow:\n    \"\"\"Workflow to sync Thingiverse.\"\"\"\n\n    @workflow.run")
content = content.replace("class SyncCults3dWorkflow:\\n    \"\"\"Workflow to sync Cults3d.\"\"\"\n\n    @workflow.run", "class SyncCults3dWorkflow:\n    \"\"\"Workflow to sync Cults3d.\"\"\"\n\n    @workflow.run")
content = content.replace("class SyncMinihoarderWorkflow:\\n    \"\"\"Workflow to sync Minihoarder.\"\"\"\n\n    @workflow.run", "class SyncMinihoarderWorkflow:\n    \"\"\"Workflow to sync Minihoarder.\"\"\"\n\n    @workflow.run")
content = content.replace("class SyncLocalWorkflow:\\n    \"\"\"Workflow to sync Local.\"\"\"\n\n    @workflow.run", "class SyncLocalWorkflow:\n    \"\"\"Workflow to sync Local.\"\"\"\n\n    @workflow.run")

content = content.replace("async def run(self) -> List[dict[str, Any]]:\\n        \"\"\"Run the workflow.\"\"\"\n        return", "async def run(self) -> List[dict[str, Any]]:\n        \"\"\"Run the workflow.\"\"\"\n        return")

with open("src/worker/temporal_workflows.py", "w") as f:
    f.write(content)

with open("tests/unit/test_main_sync.py", "r") as f:
    content = f.read()

content = content.replace("def mock_temporal_client():\\n    \"\"\"Mock the Temporal client.\"\"\"\n    with", "def mock_temporal_client():\n    \"\"\"Mock the Temporal client.\"\"\"\n    with")

with open("tests/unit/test_main_sync.py", "w") as f:
    f.write(content)
