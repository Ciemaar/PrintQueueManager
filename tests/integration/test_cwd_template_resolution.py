import os
import subprocess
import sys


def test_template_resolution_from_different_cwd(tmp_path):
    """Verify app resolves templates correctly from different CWD."""
    # Create a dummy script inside a temp directory that tries to render the index template
    test_script = tmp_path / "run_fastapi.py"

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    script_content = f"""
import sys
sys.path.insert(0, '{project_root}')

import os
# Ensure we use an in-memory SQLite DB by patching the get_db dependency
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import Base

engine = create_engine("sqlite:///./temp_integration.db")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi.testclient import TestClient
from src.app.main import app
from src.app.database import get_db

app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)

# Make a request to the root endpoint, which renders the index.html template
response = client.get("/")

if response.status_code == 200 and "Print Queue Manager" in response.text:
    print("SUCCESS: Template resolved successfully.")
    sys.exit(0)
else:
    print(f"FAILED: Status code {{response.status_code}}")
    sys.exit(1)
"""
    test_script.write_text(script_content)

    # Change to a completely different directory (the temp dir) to run the script
    # This proves that `src/app/templates` is resolved via absolute paths (__file__)
    # rather than relying on `os.getcwd()`.
    result = subprocess.run(
        [sys.executable, str(test_script)], cwd=tmp_path, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Template resolution failed: {result.stderr}\n{result.stdout}"
    assert "SUCCESS" in result.stdout
