import os

def replace_utcnow(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    content = content.replace("datetime.utcnow()", "datetime.now(datetime.UTC)")

    with open(filepath, 'w') as f:
        f.write(content)

replace_utcnow("src/app/main.py")
replace_utcnow("tests/unit/test_main.py")
