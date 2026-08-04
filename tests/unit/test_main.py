"""Unit tests for the FastAPI application main routes."""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.database import Base, get_db
from src.app.main import app
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


def test_reorder_job():
    """Verify that posting to the reorder route updates the user_priority float appropriately."""
    db = TestingSessionLocal()
    # Create three jobs with default priority 0
    job1 = PrintJob(title="Job 1", source="Test", user_priority=1.0)
    job2 = PrintJob(title="Job 2", source="Test", user_priority=2.0)
    job3 = PrintJob(title="Job 3", source="Test", user_priority=3.0)
    db.add_all([job1, job2, job3])
    db.commit()
    db.refresh(job1)
    db.refresh(job2)
    db.refresh(job3)

    # Move job3 between job1 and job2
    response = client.post(
        f"/jobs/{job3.id}/reorder", data={"above_id": str(job1.id), "below_id": str(job2.id)}
    )
    assert response.status_code == 200

    db.expire_all()
    updated_job3 = db.query(PrintJob).filter(PrintJob.id == job3.id).first()
    assert updated_job3 is not None
    # (1.0 + 2.0) / 2.0 = 1.5
    assert getattr(updated_job3, "user_priority") == 1.5

    # Move job2 to top (above job1)
    response = client.post(f"/jobs/{job2.id}/reorder", data={"below_id": str(job1.id)})
    assert response.status_code == 200
    db.expire_all()
    updated_job2 = db.query(PrintJob).filter(PrintJob.id == job2.id).first()
    assert updated_job2 is not None

    # job1 priority is 1.0, so moving job2 above it gives `below_priority - 1.0` -> 0.0
    assert getattr(updated_job2, "user_priority") == 0.0  # 1.0 - 1.0

    # Move job1 to bottom (below job3 which is now 1.5)
    response = client.post(f"/jobs/{job1.id}/reorder", data={"above_id": str(job3.id)})
    assert response.status_code == 200
    db.expire_all()
    updated_job1 = db.query(PrintJob).filter(PrintJob.id == job1.id).first()
    assert updated_job1 is not None
    assert getattr(updated_job1, "user_priority") == 2.5  # 1.5 + 1.0

    # Non-existent job
    response = client.post("/jobs/999/reorder", data={"above_id": str(job1.id)})
    assert response.status_code == 404

    db.close()


def test_reorder_job_same_priority():
    """Verify that reordering a job between two jobs with the same priority works."""
    db = TestingSessionLocal()
    # Create three jobs with default priority 0
    job1 = PrintJob(title="Job 1", source="Test", user_priority=0.0)
    job2 = PrintJob(title="Job 2", source="Test", user_priority=0.0)
    job3 = PrintJob(title="Job 3", source="Test", user_priority=0.0)
    db.add_all([job1, job2, job3])
    db.commit()
    db.refresh(job1)
    db.refresh(job2)
    db.refresh(job3)

    # Move job3 between job1 and job2
    response = client.post(
        f"/jobs/{job3.id}/reorder", data={"above_id": str(job1.id), "below_id": str(job2.id)}
    )
    assert response.status_code == 200

    db.expire_all()
    updated_job1 = db.query(PrintJob).filter(PrintJob.id == job1.id).first()
    updated_job2 = db.query(PrintJob).filter(PrintJob.id == job2.id).first()
    updated_job3 = db.query(PrintJob).filter(PrintJob.id == job3.id).first()

    assert updated_job1 is not None
    assert updated_job2 is not None
    assert updated_job3 is not None

    p1 = getattr(updated_job1, "user_priority")
    p2 = getattr(updated_job2, "user_priority")
    p3 = getattr(updated_job3, "user_priority")

    # Since they were 0.0, a collision should have been detected,
    # causing a normalization.
    # Because updated_at is descending, initial order is:
    # 1. Job 3 (created last, highest updated_at, priority 1.0)
    # 2. Job 2 (priority 2.0)
    # 3. Job 1 (priority 3.0)
    # When we move Job 3 between Job 1 and Job 2:
    # above_job = Job 1 (priority 3.0)
    # below_job = Job 2 (priority 2.0)
    # The midpoint user_priority will be 2.5
    # Since we sort by user_priority ASCENDING:
    # Job 2 (2.0) -> Job 3 (2.5) -> Job 1 (3.0)
    assert p2 < p3 < p1

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
        title="Test Job",
        source="Test",
        status=PrintStatus.DELETED,
        deleted_at=datetime.now(timezone.utc),
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
        title="Test Job",
        source="Test",
        status=PrintStatus.PRINTED,
        deleted_at=datetime.now(timezone.utc),
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


def test_undelete_job_not_found():
    """Verify that undeleting a non-existent job safely returns an empty string and causes no side effects."""
    db = TestingSessionLocal()
    initial_count = db.query(PrintJob).count()

    response = client.post("/jobs/999/undelete")
    assert response.status_code == 200
    assert response.content == b""

    # Verify no unintended database modifications occurred
    final_count = db.query(PrintJob).count()
    assert initial_count == 0
    assert final_count == 0

    db.close()


def test_read_deleted_jobs():
    """Verify that the deleted jobs view accurately filters and displays records."""
    db = TestingSessionLocal()
    job1 = PrintJob(
        title="Deleted Job 1",
        source="Test",
        status=PrintStatus.DELETED,
        deleted_at=datetime.now(timezone.utc),
    )
    job2 = PrintJob(
        title="Skipped Job",
        source="Test",
        status=PrintStatus.SKIPPED,
        deleted_at=datetime.now(timezone.utc),
    )
    job3 = PrintJob(
        title="Printed Job",
        source="Test",
        status=PrintStatus.PRINTED,
        deleted_at=datetime.now(timezone.utc),
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
