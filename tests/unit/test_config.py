"""Unit tests for application configuration."""

import os

from src.app.config import Settings


def test_settings_default_database_url_is_safe():
    """Ensure that the default database_url is safe and doesn't contain hardcoded credentials."""
    # Force empty environment for this test to check the default value
    old_db_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    try:
        # Create a new Settings instance.
        # It should fall back to its internal defaults since DATABASE_URL is not in env.
        settings = Settings()

        bad_url = "postgresql://printqueue:password@localhost:5432/printqueue"

        assert settings.database_url != bad_url, "DATABASE_URL still contains default password"
        assert "password" not in settings.database_url.lower(), "DATABASE_URL contains 'password'"

    finally:
        # Restore environment
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
