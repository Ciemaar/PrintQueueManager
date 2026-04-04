"""Unit tests for the FastAPI application main routes."""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.main import app
from src.app.database import Base, get_db
from src.app.models import PrintJob, PrintStatus, ServiceConfig

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


def test_read_main_show_printed():
    """Verify that the main view respects the show_printed query parameter."""
    db = TestingSessionLocal()
    job1 = PrintJob(title="Test Job 1", source="Test", status=PrintStatus.TO_BE_PRINTED)
    job2 = PrintJob(title="Test Job 2", source="Test", status=PrintStatus.PRINTED)
    db.add(job1)
    db.add(job2)
    db.commit()

    response = client.get("/?show_printed=true")
    assert response.status_code == 200
    assert b"Test Job 1" in response.content
    assert b"Test Job 2" in response.content

    response_no_printed = client.get("/")
    assert response_no_printed.status_code == 200
    assert b"Test Job 1" in response_no_printed.content
    assert b"Test Job 2" not in response_no_printed.content

    # Test hx-request
    response_hx = client.get("/", headers={"hx-request": "true"})
    assert response_hx.status_code == 200
    assert b"Test Job 1" in response_hx.content
    assert (
        b"Local 3D Print Queue Manager" not in response_hx.content
    )  # Check it's just the table rows


def test_undelete_job_from_deleted():
    """Verify that a DELETED job gets restored to TO BE PRINTED state."""
    db = TestingSessionLocal()
    job = PrintJob(
        title="Test Job", source="Test", status=PrintStatus.DELETED, deleted_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(f"/jobs/{job.id}/undelete")
    assert response.status_code == 200

    db.expire_all()
    undeleted_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert undeleted_job is not None
    assert undeleted_job.status == PrintStatus.TO_BE_PRINTED  # type: ignore
    assert undeleted_job.deleted_at is None
    db.close()


def test_undelete_job_from_printed():
    """Verify that a PRINTED job gets restored to PRINT AGAIN state."""
    db = TestingSessionLocal()
    job = PrintJob(
        title="Test Job", source="Test", status=PrintStatus.PRINTED, deleted_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(f"/jobs/{job.id}/undelete")
    assert response.status_code == 200

    db.expire_all()
    undeleted_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert undeleted_job is not None
    assert undeleted_job.status == PrintStatus.PRINT_AGAIN  # type: ignore
    assert undeleted_job.deleted_at is None
    db.close()


def test_read_deleted_jobs():
    """Verify that the deleted jobs view accurately filters and displays records."""
    db = TestingSessionLocal()
    job1 = PrintJob(
        title="Deleted Job 1",
        source="Test",
        status=PrintStatus.DELETED,
        deleted_at=datetime.utcnow(),
    )
    job2 = PrintJob(
        title="Skipped Job", source="Test", status=PrintStatus.SKIPPED, deleted_at=datetime.utcnow()
    )
    job3 = PrintJob(
        title="Printed Job", source="Test", status=PrintStatus.PRINTED, deleted_at=datetime.utcnow()
    )
    db.add(job1)
    db.add(job2)
    db.add(job3)
    db.commit()

    # Initial page load with no params should show all 3
    response = client.get("/deleted")
    assert response.status_code == 200
    assert b"Deleted Job 1" in response.content
    assert b"Skipped Job" in response.content
    assert b"Printed Job" in response.content

    # HTMX request sending only show_skipped and show_deleted (so show_printed is absent/false)
    response_no_printed = client.get(
        "/deleted?show_skipped=true&show_deleted=true", headers={"hx-request": "true"}
    )
    assert response_no_printed.status_code == 200
    assert b"Deleted Job 1" in response_no_printed.content
    assert b"Skipped Job" in response_no_printed.content
    assert b"Printed Job" not in response_no_printed.content

    # HTMX request sending none of them
    response_none = client.get("/deleted", headers={"hx-request": "true"})
    assert response_none.status_code == 200
    assert b"Deleted Job 1" not in response_none.content
    assert b"Skipped Job" not in response_none.content
    assert b"Printed Job" not in response_none.content


def test_settings_page_get():
    """Verify that the settings configuration page renders successfully."""
    response = client.get("/settings")
    assert response.status_code == 200
    assert b"Service Configuration" in response.content
    assert b"MakerWorld" in response.content


def test_update_settings_new_config():
    """Verify that posting valid configuration creates a new DB record if missing."""
    db = TestingSessionLocal()

    response = client.post(
        "/settings/update",
        data={
            "service_name": "makerworld",
            "enabled": "1",
            "target_url": "http://my-target.com",
            "credential": "test_session_cookie",
        },
    )
    assert response.status_code == 200
    assert b"Settings saved for Makerworld!" in response.content

    config = db.query(ServiceConfig).filter(ServiceConfig.service_name == "makerworld").first()
    assert config is not None
    assert getattr(config, "enabled") == 1
    assert getattr(config, "target_url") == "http://my-target.com"
    assert getattr(config, "credential") == "test_session_cookie"
    db.close()


def test_update_settings_existing_config_no_credential():
    """Verify that posting updates an existing DB record and preserves credential if empty."""
    db = TestingSessionLocal()
    existing = ServiceConfig(
        service_name="makerworld", enabled=0, target_url="old_url", credential="old_credential"
    )
    db.add(existing)
    db.commit()

    response = client.post(
        "/settings/update",
        data={
            "service_name": "makerworld",
            "enabled": "1",
            "target_url": "new_url",
            "credential": "",
        },
    )
    assert response.status_code == 200

    db.expire_all()
    config = db.query(ServiceConfig).filter(ServiceConfig.service_name == "makerworld").first()
    assert getattr(config, "enabled") == 1
    assert getattr(config, "target_url") == "new_url"
    assert getattr(config, "credential") == "old_credential"
    db.close()
