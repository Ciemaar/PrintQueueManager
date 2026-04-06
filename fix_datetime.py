import os

def fix_datetime(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Python 3.10 and 3.11 handle `datetime.timezone.utc`. `datetime.UTC` was introduced in 3.11,
    # but the environment here says Python 3.12... wait, why `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'`?
    # Ah! `datetime.UTC` is an attribute of the `datetime` module, NOT the `datetime.datetime` class!
    # We did `from datetime import datetime`.
    # So `datetime.now(datetime.UTC)` is trying to access `.UTC` on the `datetime` class.
    # It should be `datetime.now(timezone.utc)`.

    content = content.replace("datetime.now(datetime.UTC)", "datetime.now(timezone.utc)")

    # Add import timezone if missing
    if "from datetime import datetime" in content and "timezone" not in content:
        content = content.replace("from datetime import datetime", "from datetime import datetime, timezone")

    with open(filepath, 'w') as f:
        f.write(content)

fix_datetime("src/app/models/__init__.py")
fix_datetime("src/app/main.py")
fix_datetime("tests/unit/test_main.py")
