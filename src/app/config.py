import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://printqueue:password@localhost:5432/printqueue")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    watch_directory: str = os.getenv("WATCH_DIRECTORY", "./watched_folder")

    # API Authentication & Session Configurations
    thingiverse_api_token: str = os.getenv("THINGIVERSE_API_TOKEN", "")
    makerworld_cookie: str = os.getenv("MAKERWORLD_COOKIE", "")
    printables_cookie: str = os.getenv("PRINTABLES_COOKIE", "")
    cults3d_cookie: str = os.getenv("CULTS3D_COOKIE", "")
    minihoarder_cookie: str = os.getenv("MINIHOARDER_COOKIE", "")

settings = Settings()
