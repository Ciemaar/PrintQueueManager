from unittest.mock import MagicMock, patch

from src.worker.celery_app import generate_local_thumbnails


@patch("src.worker.celery_app.SessionLocal")
@patch("src.worker.celery_app.os.path.exists")
@patch("src.worker.celery_app.generate_thumbnail")
@patch("src.worker.celery_app.get_thumbnail_file_path")
def test_generate_local_thumbnails_success(mock_get_path, mock_generate, mock_exists, mock_session):
    """Test processing database to generate missing thumbnails."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db

    # Create fake job
    class FakeJob:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    job1 = FakeJob(id=1, file_path="test1.stl", title="Test 1", source="Local")
    job2 = FakeJob(id=2, file_path="test2.stl", title="Test 2", source="Local")
    job3 = FakeJob(id=3, file_path=None, title="Test 3", source="Local")

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [job1, job2, job3]
    mock_db.query.return_value = mock_query

    mock_get_path.return_value = "/fake/thumb/path.png"

    # For job 1: thumb doesn't exist, file does exist -> generates
    # For job 2: thumb exists -> skips
    # For job 3: no file_path -> skips
    mock_generate.return_value = True

    # Need an easier way to mock this specific logic, let's just make it simple
    mock_exists.side_effect = [
        False,
        True,
        True,
        True,
    ]  # job1 thumb missing, job1 file exists, job2 thumb exists

    count = generate_local_thumbnails()

    assert count == 1
    mock_generate.assert_called_once_with("test1.stl", 1)
    mock_db.close.assert_called_once()


@patch("src.worker.celery_app.SessionLocal")
def test_generate_local_thumbnails_exception(mock_session):
    """Test error handling during generation."""
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_db.query.side_effect = Exception("DB Error")

    count = generate_local_thumbnails()

    assert count == 0
    mock_db.close.assert_called_once()
