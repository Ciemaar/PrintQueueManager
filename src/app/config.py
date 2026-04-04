"""Configuration settings for the Print Queue Manager application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    database_url: str = "postgresql://printqueue:password@localhost:5432/printqueue"
    redis_url: str = "redis://localhost:6379/0"
    ollama_host: str = "http://localhost:11434"
    watch_directory: str = "./watched_folder"

    # API Authentication & Session Configurations
    thingiverse_api_token: str = ""
    makerworld_cookie: str = ""
    printables_cookie: str = ""
    cults3d_cookie: str = ""
    minihoarder_cookie: str = ""
    demo_mode: bool = False

    # Synchronization Schedules (Cron format, defaulting to once a week on Sunday at midnight)
    makerworld_sync_cron: str = "0 0 * * 0"
    printables_sync_cron: str = "0 0 * * 0"
    thingiverse_sync_cron: str = "0 0 * * 0"
    cults3d_sync_cron: str = "0 0 * * 0"
    minihoarder_sync_cron: str = "0 0 * * 0"

    # Debugging
    verbose: bool = False


settings = Settings()
