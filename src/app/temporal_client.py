"""Temporal client initialization for FastAPI app."""

from temporalio.client import Client
from src.app.config import settings

_temporal_client: Client | None = None

async def get_temporal_client() -> Client:
    """Get or initialize the Temporal client."""
    global _temporal_client
    if _temporal_client is None:
        _temporal_client = await Client.connect(settings.temporal_target)
    return _temporal_client
