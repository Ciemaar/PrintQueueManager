import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://printqueue:password@localhost:5432/printqueue")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    watch_directory: str = os.getenv("WATCH_DIRECTORY", "./watched_folder")

settings = Settings()
