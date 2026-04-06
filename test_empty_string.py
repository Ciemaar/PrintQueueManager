from fastapi.testclient import TestClient
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_empty.db"
from src.app.main import app
from src.app.models import PrintJob, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./test_empty.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
# Is it possible that the javascript IS sending an empty string?
# "const aboveId = prevEl ? prevEl.getAttribute('data-job-id') : '';"
# "if (aboveId) formData.append('above_id', aboveId);"
# What if `prevEl` is grabbing something that doesn't have `data-job-id`?
# Then `aboveId` is `null`.
# "if (aboveId)" handles `null`, `undefined`, `''`.
# But wait! `getAttribute` returns `null` if the attribute doesn't exist!
# In JS, `null` is falsy. So it won't append.

# Let's verify what happens if `prevEl` is a header row `<tr>`!
