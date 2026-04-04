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

# Emulate test payload: Move job3 between job1 and job2
# Since they were 0.0, normalization sets them to job3=1.0, job2=2.0, job1=3.0 (reverse order created_at)
# above_job is job1 (now 3.0), below_job is job2 (now 2.0).
# Wait, if above_job is 3.0 and below_job is 2.0, midpoint is 2.5!
# But the order should be job1 (above), job3 (middle), job2 (below).
# If ascending sort, user_priority 1 < 2 < 3.
# job1 is 3.0, job2 is 2.0. To place job3 between them, job3 gets 2.5.
# Then job3 (2.5) comes after job2 (2.0) and before job1 (3.0) in ascending sort!
# So ascending order would be: job3 (1.0), job2 (2.0), job3 (2.5), job1 (3.0) -> job2, job3, job1.
# Wait, if job1 is 3.0 and job2 is 2.0, ascending sort means job2 comes before job1.
# But job1 was supposed to be ABOVE job2!

print("before normalization order:", [j.title for j in db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()])
