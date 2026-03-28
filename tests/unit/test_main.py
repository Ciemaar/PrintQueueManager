"""Unit tests for the FastAPI application main routes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.main import app
from src.app.database import Base, get_db
from src.app.models import PrintJob, PrintStatus

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Yield a database session connected to the local test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Set up and tear down the test database schema before/after each test execution."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_read_main():
    """Verify the root index page renders correctly with the application title."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Local 3D Print Queue Manager" in response.content


def test_delete_job():
    """Verify that posting to a delete route properly marks a job as DELETED in the database."""
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test")
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(f"/jobs/{job.id}/delete")
    assert response.status_code == 200

    db.expire_all()
    deleted_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert deleted_job is not None
    assert deleted_job.status == PrintStatus.DELETED  # type: ignore
    db.close()


def test_update_status():
    """Verify that posting to the status route correctly updates the status text."""
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test", status=PrintStatus.TO_BE_PRINTED)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Note: HTMX toggle requests use POST and return 200 OK
    response = client.post(f"/jobs/{job.id}/status", data={"status": "PRINT IN PROGRESS"})
    assert response.status_code == 200

    # Ensure to refresh db session when querying to get the updated row
    db.expire_all()
    updated_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert updated_job is not None
    assert updated_job.status == PrintStatus.PRINT_IN_PROGRESS  # type: ignore
    db.close()


def test_update_status_invalid():
    """Verify that posting an invalid status is ignored safely."""
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test", status=PrintStatus.TO_BE_PRINTED)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(f"/jobs/{job.id}/status", data={"status": "MADE UP STATUS"})
    assert response.status_code == 200

    db.expire_all()
    updated_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert updated_job is not None
    assert updated_job.status == PrintStatus.TO_BE_PRINTED  # type: ignore
    db.close()


def test_update_notes():
    """Verify that posting to the notes route correctly updates material and timing notes."""
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test", status=PrintStatus.TO_BE_PRINTED)
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(
        f"/jobs/{job.id}/notes", data={"material_notes": "PLA", "timing_notes": "2 hrs"}
    )
    assert response.status_code == 200

    db.expire_all()
    updated_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert updated_job is not None
    assert updated_job.material_notes == "PLA"  # type: ignore
    assert updated_job.timing_notes == "2 hrs"  # type: ignore
    db.close()
