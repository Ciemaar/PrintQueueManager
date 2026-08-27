"""SQLAlchemy database models for the application."""

from collections.abc import Sequence
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Session
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
    user_priority = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = Column(DateTime, nullable=True)

    @classmethod
    def get_active_jobs(cls, db: Session, show_printed: bool = False) -> Sequence["PrintJob"]:
        """
        Retrieve active (non-deleted) jobs for the main dashboard.

        This class method is the preferred pattern for encapsulating complex queries
        to keep route handlers clean and focused on view logic.
        """
        query = db.query(cls)

        if show_printed:
            query = query.filter(
                cls.status.in_(
                    [
                        PrintStatus.TO_BE_PRINTED,
                        PrintStatus.PRINT_IN_PROGRESS,
                        PrintStatus.PRINT_AGAIN,
                        PrintStatus.PRINTED,
                    ]
                )
            )
        else:
            query = query.filter(
                cls.status.in_(
                    [
                        PrintStatus.TO_BE_PRINTED,
                        PrintStatus.PRINT_IN_PROGRESS,
                        PrintStatus.PRINT_AGAIN,
                    ]
                )
            )

        return query.order_by(cls.user_priority.asc().nullsfirst(), cls.updated_at.desc()).all()

    @classmethod
    def get_deleted_jobs(
        cls, db: Session, show_printed: bool, show_skipped: bool, show_deleted: bool
    ) -> Sequence["PrintJob"]:
        """
        Retrieve jobs for the deleted view, filtered by type.

        This class method is the preferred pattern for encapsulating complex queries
        to keep route handlers clean and focused on view logic.
        """
        status_filters = []
        if show_printed:
            status_filters.append(PrintStatus.PRINTED)
        if show_skipped:
            status_filters.append(PrintStatus.SKIPPED)
        if show_deleted:
            status_filters.append(PrintStatus.DELETED)

        if not status_filters:
            return []

        return (
            db.query(cls)
            .filter(cls.status.in_(status_filters))
            .order_by(cls.deleted_at.desc().nullslast())
            .all()
        )

    @classmethod
    def get_by_id(cls, db: Session, job_id: int) -> "PrintJob | None":
        """Retrieve a single PrintJob by its ID."""
        return db.query(cls).filter(cls.id == job_id).first()

    @classmethod
    def get_jobs_for_normalization(cls, db: Session) -> Sequence["PrintJob"]:
        """Retrieve all active jobs ordered for priority normalization."""
        return (
            db.query(cls)
            .filter(cls.status != PrintStatus.DELETED)
            .order_by(cls.user_priority.asc(), cls.updated_at.desc())
            .all()
        )

class ServiceConfig(Base):
    """Represents the configuration for an external model source."""

    __tablename__ = "service_configs"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, unique=True, index=True)
    enabled: int = Column(Integer, default=0) # type: ignore  # SQLite compatible boolean 1/0
    credential: str | None = Column(String, nullable=True) # type: ignore
    target_url: str | None = Column(String, nullable=True) # type: ignore
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
