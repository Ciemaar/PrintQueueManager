from unittest.mock import MagicMock, patch

from src.app.models import PrintJob
from src.worker.celery_app import generate_local_thumbnails


@patch("src.worker.celery_app.SessionLocal")
@patch("src.worker.celery_app.Path")
@patch("src.worker.celery_app.generate_thumbnail")
def test_generate_local_thumbnails_success(mock_generate, mock_path, mock_session):
    """Test successful generation of thumbnails for local missing files."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    # Mock job
    job1 = MagicMock(spec=PrintJob)
    job1.source = "Local"
    job1.file_path = "/path/to/file.stl"
    job1.thumbnail_url = None

    mock_db.query.return_value.filter.return_value.all.return_value = [job1]

    # Mock Path
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_file.return_value = True
    mock_path.return_value = mock_path_instance

    mock_generate.return_value = True

    count = generate_local_thumbnails()

    assert count == 1
    mock_generate.assert_called_once()
    mock_db.commit.assert_called_once()


@patch("src.worker.celery_app.SessionLocal")
def test_generate_local_thumbnails_exception(mock_session):
    """Test exception handling during thumbnail generation loop."""
    from sqlalchemy.exc import SQLAlchemyError
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_db.query.side_effect = SQLAlchemyError("DB Error")

    count = generate_local_thumbnails()

    assert count == 0
    mock_db.rollback.assert_called_once()
