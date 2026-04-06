"""SQLAlchemy database models for the application."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.types import JSON

from src.app.database import Base


class PrintStatus(str, Enum):
    """Enumeration of possible states for a PrintJob."""

    TO_BE_PRINTED = "TO BE PRINTED"
    PRINT_IN_PROGRESS = "PRINT IN PROGRESS"
    PRINT_AGAIN = "PRINT AGAIN"
    PRINTED = "PRINTED"
    SKIPPED = "SKIPPED"
    DELETED = "DELETED"


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

    # Status mapped to the PrintStatus Enum
    status = Column(SQLAlchemyEnum(PrintStatus), default=PrintStatus.TO_BE_PRINTED)

    # Notes
    material_notes = Column(String, nullable=True)
    timing_notes = Column(String, nullable=True)

    # User-defined ordering via drag-and-drop
    user_priority = Column(Float, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = Column(DateTime, nullable=True)
