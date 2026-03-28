with open("src/worker/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleIntervalSpec, ScheduleSpec" in line:
        new_lines.append("from temporalio.client import (\n")
        new_lines.append("    Client,\n")
        new_lines.append("    Schedule,\n")
        new_lines.append("    ScheduleActionStartWorkflow,\n")
        new_lines.append("    ScheduleIntervalSpec,\n")
        new_lines.append("    ScheduleSpec,\n")
        new_lines.append(")\n")
    elif "\"\"\"Setup periodic schedules if they don't already exist.\"\"\"" in line:
        new_lines.append(line.replace("\"\"\"Setup periodic schedules if they don't already exist.\"\"\"", "\"\"\"Set up periodic schedules if they do not already exist.\"\"\""))
    else:
        new_lines.append(line)

with open("src/worker/main.py", "w") as f:
    f.writelines(new_lines)
