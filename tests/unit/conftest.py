import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app import database

@pytest.fixture(scope="session", autouse=True)
def force_sqlite_db():
    """Force all database operations to use an in-memory SQLite database during tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch the database module globals
    database.engine = engine
    database.SessionLocal = TestingSessionLocal

    # Ensure tables are created
    from src.app.models import Base
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
