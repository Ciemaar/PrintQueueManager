import logging
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_sort.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base

engine = create_engine("sqlite:///./test_sort.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
import time
job1 = PrintJob(title="Job 1", source="Test", user_priority=0.0)
db.add(job1)
db.commit()
time.sleep(0.1)

job2 = PrintJob(title="Job 2", source="Test", user_priority=0.0)
db.add(job2)
db.commit()
time.sleep(0.1)

job3 = PrintJob(title="Job 3", source="Test", user_priority=0.0)
db.add(job3)
db.commit()

# Print original order
def print_order(msg):
    jobs = db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()
    print(f"\n--- {msg} ---")
    for j in jobs:
        print(f"ID: {j.id}, Title: {j.title}, Priority: {getattr(j, 'user_priority')}, Updated: {getattr(j, 'updated_at')}")

print_order("Original")

# Simulate moving Job 2 to the top
from src.app.main import app, reorder_job
from fastapi.testclient import TestClient

client = TestClient(app)

# The JS sends 'below_id' of the item that WAS at the top, which is Job 3 (because it's sorted by updated_at.desc()!)
# Wait, let's check the original order to see who is at the top.
# Job 3 is at the top! Then Job 2, then Job 1.
# So if we move Job 2 to the top, it goes ABOVE Job 3.
# below_id = Job 3.

response = client.post(f"/jobs/{job2.id}/reorder", data={"below_id": str(job3.id)})
print(f"\nResponse: {response.status_code}")

print_order("After dragging Job 2 to top")

# Notice that the priority of Job 2 is still 0.0 in the output above!
# WHY?
# Let's check `reorder_job` logic.
# "elif below_job: below_priority = getattr(below_job, 'user_priority'); setattr(job, 'user_priority', below_priority - 1.0)"
# Let's print out what actually happened to Job 2 in the DB:
db.expire_all()
j2 = db.query(PrintJob).get(2)
print("DB priority of job 2:", getattr(j2, 'user_priority'))
