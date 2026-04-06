import os
os.environ["DATABASE_URL"] = "sqlite:///./test_sort.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base

engine = create_engine("sqlite:///./test_sort.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

# Print DB priorities manually to see why they didn't show as -1.0 earlier
jobs = db.query(PrintJob).all()
for j in jobs:
    print(j.id, getattr(j, 'user_priority'))

jobs_sorted = db.query(PrintJob).order_by(PrintJob.user_priority.asc(), PrintJob.updated_at.desc()).all()
for j in jobs_sorted:
    print("Sorted", j.id, getattr(j, 'user_priority'))
