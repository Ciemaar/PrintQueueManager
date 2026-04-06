import os
import threading
from unittest.mock import MagicMock
import sys
import time

sys.modules['src.worker.celery_app'] = MagicMock()
os.environ["DATABASE_URL"] = "sqlite:///./test_ui_reorder.db"
os.environ["PYTHONPATH"] = "."

import uvicorn
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.models import PrintJob, Base
from src.app.main import app

engine = create_engine("sqlite:///./test_ui_reorder.db", connect_args={"check_same_thread": False})
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
    # 0.0 default priorities
    job1 = PrintJob(title="Job A (1)", source="Test", user_priority=0.0)
    db.add(job1)
    db.commit()
    time.sleep(0.1)
    job2 = PrintJob(title="Job B (2)", source="Test", user_priority=0.0)
    db.add(job2)
    db.commit()
    time.sleep(0.1)
    job3 = PrintJob(title="Job C (3)", source="Test", user_priority=0.0)
    db.add(job3)
    db.commit()
    db.close()

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("http://127.0.0.1:8002")
            page.wait_for_selector("#job-list tr")

            rows = page.locator("#job-list tr")

            # Initial order should be Job C, Job B, Job A because of updated_at.desc()
            print("Initial UI order:")
            for i in range(3):
                print(f"{i}: {rows.nth(i).locator('strong').inner_text()}")

            # Drag the SECOND item (Job B) to the TOP (above Job C)
            handles = page.locator(".drag-handle")
            source_handle = handles.nth(1) # Second item
            target_handle = handles.nth(0) # First item

            source_box = source_handle.bounding_box()
            target_box = target_handle.bounding_box()

            # Perform drag and drop slightly above the target
            page.mouse.move(source_box["x"] + source_box["width"] / 2, source_box["y"] + source_box["height"] / 2)
            page.mouse.down()
            page.mouse.move(target_box["x"] + target_box["width"] / 2, target_box["y"] + target_box["height"] / 2 - 10)
            page.mouse.up()

            # Wait a bit for the fetch to resolve
            page.wait_for_timeout(1000)

            print("\nOrder before refresh:")
            for i in range(3):
                print(f"{i}: {rows.nth(i).locator('strong').inner_text()}")

            # Refresh the page
            page.reload()
            page.wait_for_selector("#job-list tr")

            rows = page.locator("#job-list tr")
            print("\nOrder after refresh:")
            for i in range(3):
                print(f"{i}: {rows.nth(i).locator('strong').inner_text()}")

        finally:
            browser.close()

if __name__ == "__main__":
    setup_db()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    verify_ui()
