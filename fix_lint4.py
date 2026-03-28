import re

with open("src/worker/temporal_workflows.py", "r") as f:
    content = f.read()

content = content.replace("class SyncMakerworldWorkflow:\\n    \"\"\"Workflow to sync Makerworld.\"\"\"", "class SyncMakerworldWorkflow:\n    \"\"\"Workflow to sync Makerworld.\"\"\"")
content = content.replace("class SyncPrintablesWorkflow:\\n    \"\"\"Workflow to sync Printables.\"\"\"", "class SyncPrintablesWorkflow:\n    \"\"\"Workflow to sync Printables.\"\"\"")
content = content.replace("class SyncThingiverseWorkflow:\\n    \"\"\"Workflow to sync Thingiverse.\"\"\"", "class SyncThingiverseWorkflow:\n    \"\"\"Workflow to sync Thingiverse.\"\"\"")
content = content.replace("class SyncCults3dWorkflow:\\n    \"\"\"Workflow to sync Cults3d.\"\"\"", "class SyncCults3dWorkflow:\n    \"\"\"Workflow to sync Cults3d.\"\"\"")
content = content.replace("class SyncMinihoarderWorkflow:\\n    \"\"\"Workflow to sync Minihoarder.\"\"\"", "class SyncMinihoarderWorkflow:\n    \"\"\"Workflow to sync Minihoarder.\"\"\"")
content = content.replace("class SyncLocalWorkflow:\\n    \"\"\"Workflow to sync Local.\"\"\"", "class SyncLocalWorkflow:\n    \"\"\"Workflow to sync Local.\"\"\"")

with open("src/worker/temporal_workflows.py", "w") as f:
    f.write(content)

with open("tests/unit/test_main_sync.py", "r") as f:
    content = f.read()

content = content.replace("def mock_temporal_client():\\n    \"\"\"Mock the Temporal client.\"\"\"", "def mock_temporal_client():\n    \"\"\"Mock the Temporal client.\"\"\"")

with open("tests/unit/test_main_sync.py", "w") as f:
    f.write(content)
