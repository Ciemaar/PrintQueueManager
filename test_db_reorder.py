import logging
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_db_reorder.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base
from src.app.main import app, reorder_job
from fastapi.testclient import TestClient

engine = create_engine("sqlite:///./test_db_reorder.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.DEBUG)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
import time
job1 = PrintJob(title="Job 1 (0.0)", source="Test", user_priority=0.0)
db.add(job1)
db.commit()
time.sleep(0.1)

job2 = PrintJob(title="Job 2 (0.0)", source="Test", user_priority=0.0)
db.add(job2)
db.commit()
time.sleep(0.1)

job3 = PrintJob(title="Job 3 (0.0)", source="Test", user_priority=0.0)
db.add(job3)
db.commit()

client = TestClient(app)

print("\n--- DB STATE AFTER INIT ---")
jobs = db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()
for j in jobs:
    print(f"ID: {j.id}, Title: {j.title}, Priority: {getattr(j, 'user_priority')}")

# Move Job 2 to the top!
# In the UI, order is 3, 2, 1
# Moving 2 to the top means above 3.
# So above_id = None, below_id = 3
response = client.post("/jobs/2/reorder", data={"below_id": "3"})

db.expire_all()
print("\n--- DB STATE AFTER FIRST DRAG (Job 2 to top) ---")
jobs = db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()
for j in jobs:
    print(f"ID: {j.id}, Title: {j.title}, Priority: {getattr(j, 'user_priority')}")

# Now wait, what if we move the NEXT second item to the top?
# The order is now: Job 2 (-1.0), Job 3 (0.0), Job 1 (0.0)
# Second item is Job 3.
# Move Job 3 to the top.
# above_id = None, below_id = 2
response = client.post("/jobs/3/reorder", data={"below_id": "2"})

db.expire_all()
print("\n--- DB STATE AFTER SECOND DRAG (Job 3 to top) ---")
jobs = db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()
for j in jobs:
    print(f"ID: {j.id}, Title: {j.title}, Priority: {getattr(j, 'user_priority')}")
