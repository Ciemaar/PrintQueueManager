"""Configuration settings for the Print Queue Manager application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    database_url: str = "postgresql://printqueue:password@localhost:5432/printqueue"
    temporal_target: str = "localhost:7233"
    ollama_host: str = "http://localhost:11434"
    watch_directory: str = "./watched_folder"

    # API Authentication & Session Configurations
    thingiverse_api_token: str = ""
    makerworld_cookie: str = ""
    printables_cookie: str = ""
    cults3d_cookie: str = ""
    minihoarder_cookie: str = ""
    demo_mode: bool = False

    # Synchronization Intervals (in seconds, defaulting to 1 week = 604800 seconds)
    makerworld_sync_interval: float = 604800.0
    printables_sync_interval: float = 604800.0
    thingiverse_sync_interval: float = 604800.0
    cults3d_sync_interval: float = 604800.0
    minihoarder_sync_interval: float = 604800.0

    # Debugging
    verbose: bool = False


settings = Settings()
