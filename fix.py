with open("src/app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("<<<<<<< Updated upstream"):
        pass
    elif line.startswith("======="):
        skip = True
    elif line.startswith(">>>>>>> Stashed changes"):
        skip = False
    elif not skip:
        if "jobs = query.order_by(PrintJob.created_at.desc()).all()" in line:
            new_lines.append("    jobs = query.order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()\n")
        else:
            new_lines.append(line)

with open("src/app/main.py", "w") as f:
    f.writelines(new_lines)
