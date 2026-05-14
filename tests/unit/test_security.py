import html
import urllib.parse

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_trigger_sync_xss():
    """Verify that the trigger_sync endpoint escapes user input to prevent XSS."""
    # Use a payload that is safe in a URL path if encoded but still requires escaping
    malicious_input = "xss&<"
    encoded_input = urllib.parse.quote(malicious_input)
    response = client.post(f"/sync/{encoded_input}")

    assert response.status_code == 200
    expected = html.escape(malicious_input)
    assert expected in response.text
    assert malicious_input not in response.text
