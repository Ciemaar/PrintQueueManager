import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.main import app
from src.app.database import Base, get_db
from src.app.models import PrintJob

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert b"Local 3D Print Queue Manager" in response.content

def test_delete_job():
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test")
    db.add(job)
    db.commit()
    db.refresh(job)

    response = client.post(f"/jobs/{job.id}/delete")
    assert response.status_code == 200

    deleted_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert deleted_job is None
    db.close()

def test_toggle_job():
    db = TestingSessionLocal()
    job = PrintJob(title="Test Job", source="Test", is_printed=False)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Note: HTMX toggle requests use POST and return 200 OK
    response = client.post(f"/jobs/{job.id}/toggle")
    assert response.status_code == 200

    # Ensure to refresh db session when querying to get the updated row
    db.expire_all()
    updated_job = db.query(PrintJob).filter(PrintJob.id == job.id).first()
    assert updated_job is not None
    assert updated_job.is_printed is True
    db.close()
