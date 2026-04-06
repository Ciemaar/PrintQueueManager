# Wait, `or 0.0` solves it, but wait! What if it's EXACTLY `0.0`?
# `0.0 or 0.0` is `0.0`. That's fine.
# But what if `getattr()` returns `None` when `above_job` exists?
# `None or 0.0` evaluates to `0.0`. So `TypeError` is resolved.

import os
os.environ["DATABASE_URL"] = "sqlite:///./test_empty4.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base

engine = create_engine("sqlite:///./test_empty4.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Simulate a raw SQL insert so it is NULL
db.execute(PrintJob.__table__.insert(), [{"title": "Job 1", "source": "Test", "user_priority": None}])
db.execute(PrintJob.__table__.insert(), [{"title": "Job 2", "source": "Test", "user_priority": None}])
db.execute(PrintJob.__table__.insert(), [{"title": "Job 3", "source": "Test", "user_priority": None}])
db.commit()

from src.app.main import app, reorder_job
from fastapi.testclient import TestClient

client = TestClient(app)

print("\n--- Move Job 2 to the top! ---")
response = client.post("/jobs/2/reorder", data={"below_id": "3"})
print(response.status_code)
