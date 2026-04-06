import os
import threading
from unittest.mock import MagicMock
import sys
import time

sys.modules['src.worker.celery_app'] = MagicMock()
os.environ["DATABASE_URL"] = "sqlite:///./test_ui_reorder4.db"
os.environ["PYTHONPATH"] = "."

import uvicorn
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.models import PrintJob, Base
from src.app.main import app

engine = create_engine("sqlite:///./test_ui_reorder4.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_override():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[__import__('src.app.database').app.database.get_db] = get_db_override

def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # WHAT IF it's exactly the case the user described?
    # They pull the SECOND item to the TOP.
    # What if they DO IT TWICE? Wait... The order is NOT SAVED.
    # Let's read the index.html Sortable setup VERY CAREFULLY.
    pass
