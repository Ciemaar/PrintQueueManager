import re

with open("src/app/main.py", "r") as f:
    text = f.read()

# Make sure sync_myminifactory is fully used in main.py
if '"myminifactory": sync_myminifactory' not in text:
    text = text.replace(
        'sync_tasks = {\n        "cults3d": sync_cults3d,\n        "local": sync_local,\n        "makerworld": sync_makerworld,\n        "minihoarder": sync_minihoarder,\n        "printables": sync_printables,\n        "thingiverse": sync_thingiverse,\n    }',
        'sync_tasks = {\n        "cults3d": sync_cults3d,\n        "local": sync_local,\n        "makerworld": sync_makerworld,\n        "minihoarder": sync_minihoarder,\n        "myminifactory": sync_myminifactory,\n        "printables": sync_printables,\n        "thingiverse": sync_thingiverse,\n    }'
    )

with open("src/app/main.py", "w") as f:
    f.write(text)
