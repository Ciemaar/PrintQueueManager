import re

with open("src/worker/main.py", "r") as f:
    content = f.read()

content = content.replace("from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleIntervalSpec, ScheduleSpec", "from temporalio.client import (\n    Client,\n    Schedule,\n    ScheduleActionStartWorkflow,\n    ScheduleIntervalSpec,\n    ScheduleSpec,\n)")
content = content.replace("\"\"\"Setup periodic schedules if they don't already exist.\"\"\"", "\"\"\"Set up periodic schedules if they do not already exist.\"\"\"")

with open("src/worker/main.py", "w") as f:
    f.write(content)
