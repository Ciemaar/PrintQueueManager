import logging
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.DEBUG)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
job1 = PrintJob(title="Job 1", source="Test", user_priority=0.0)
job2 = PrintJob(title="Job 2", source="Test", user_priority=0.0)
job3 = PrintJob(title="Job 3", source="Test", user_priority=0.0)
db.add_all([job1, job2, job3])
db.commit()
db.refresh(job1)
db.refresh(job2)
db.refresh(job3)

# Emulate what happens in normalization
from src.app.main import _normalize_priorities_sync
_normalize_priorities_sync(db)

db.refresh(job1)
db.refresh(job2)
db.refresh(job3)

print("job1: ", job1.id, getattr(job1, "user_priority"))
print("job2: ", job2.id, getattr(job2, "user_priority"))
print("job3: ", job3.id, getattr(job3, "user_priority"))
