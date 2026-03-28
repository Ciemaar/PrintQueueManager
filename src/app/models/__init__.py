"""SQLAlchemy database models for the application."""

from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.types import JSON
from sqlalchemy import Enum as SQLAlchemyEnum
from datetime import datetime
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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
