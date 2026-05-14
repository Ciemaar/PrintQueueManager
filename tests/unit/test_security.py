from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_trigger_sync_xss():
    """Verify that the trigger_sync endpoint escapes user input to prevent XSS."""
    malicious_input = "<script>alert('xss')</script>"
    response = client.post(f"/sync/{malicious_input}")
    assert response.status_code == 200
    # If not escaped, the response would contain the raw script tag
    # If escaped, it should contain &lt;script&gt;
    assert b"<script>" not in response.content
    assert b"&lt;script&gt;" in response.content
