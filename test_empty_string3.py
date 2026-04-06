# Ah, `nullable=True`! But in the `models.py` we have `default=0.0`.
# When the column is added via migration, existing rows get `NULL` (None).
# What happens if `user_priority` is `None`?
# In `getattr(above_job, 'user_priority')`, it returns `None`.
# Then `above_priority >= below_priority` crashes with TypeError?
# "TypeError: '>=' not supported between instances of 'NoneType' and 'float'"
# Let's test what happens if `user_priority` is None!
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_empty3.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models import PrintJob, Base

engine = create_engine("sqlite:///./test_empty3.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# If user_priority is not set, what happens? SQLAlchemy models inject default=0.0 when creating.
# Let's simulate a raw SQL insert so it is NULL
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
