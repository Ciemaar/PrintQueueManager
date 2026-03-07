from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.types import JSON
from datetime import datetime
from src.app.database import Base

class PrintJob(Base):
    __tablename__ = "print_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    source = Column(String, index=True)
    source_url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    author = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)
    is_printed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
