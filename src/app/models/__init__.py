"""SQLAlchemy database models for the application."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.types import JSON
from datetime import datetime
from src.app.database import Base


class PrintJob(Base):
    """Represents a 3D model scheduled for printing or tracked in the queue."""

    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String, index=True)
    source_url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    author = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)

    # Status can be: TO BE PRINTED, PRINT IN PROGRESS, PRINT AGAIN, PRINTED, SKIPPED, DELETED
    status = Column(String, default="TO BE PRINTED")

    # Notes
    material_notes = Column(String, nullable=True)
    timing_notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
