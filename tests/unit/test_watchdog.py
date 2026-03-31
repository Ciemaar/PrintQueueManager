"""Unit tests for the watchdog directory monitor."""

from unittest.mock import patch, MagicMock
from src.watchdog.main import PrintQueueEventHandler, main


def test_on_created_file_detected():
    """Verify on_created triggers add_to_queue for valid files."""
    handler = PrintQueueEventHandler()
    handler._add_to_queue = MagicMock()  # pylint: disable=protected-access

    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = "/fake/path/test_model.stl"

    handler.on_created(mock_event)

    handler._add_to_queue.assert_called_once_with(  # pylint: disable=protected-access
        "/fake/path/test_model.stl", "test_model.stl", False
    )


def test_on_created_ignores_directories():
    """Verify on_created ignores directory creation events."""
    handler = PrintQueueEventHandler()
    handler._add_to_queue = MagicMock()  # pylint: disable=protected-access

    mock_event = MagicMock()
    mock_event.is_directory = True
    mock_event.src_path = "/fake/path/test_dir"

    handler.on_created(mock_event)

    handler._add_to_queue.assert_not_called()  # pylint: disable=protected-access


def test_on_created_ignores_non_3d_files():
    """Verify on_created ignores non-STL/3MF files."""
    handler = PrintQueueEventHandler()
    handler._add_to_queue = MagicMock()  # pylint: disable=protected-access

    mock_event = MagicMock()
    mock_event.is_directory = False
    mock_event.src_path = "/fake/path/readme.txt"

    handler.on_created(mock_event)

    handler._add_to_queue.assert_not_called()  # pylint: disable=protected-access


@patch("src.watchdog.main.os.path.getsize")
@patch("src.watchdog.main.SessionLocal")
def test_add_to_queue_new_file(mock_session_local, mock_getsize):
    """Verify add_to_queue inserts a new job into the database."""
    mock_getsize.return_value = 1024
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate DB query returning None (file doesn't exist yet)
    mock_db.query.return_value.filter.return_value.first.return_value = None

    handler = PrintQueueEventHandler()
    handler._add_to_queue("/fake/test.stl", "test.stl")  # pylint: disable=protected-access

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("src.watchdog.main.SessionLocal")
def test_add_to_queue_existing_file(mock_session_local):
    """Verify add_to_queue skips inserting if the file is already in the database."""
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate DB query returning an existing record
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

    handler = PrintQueueEventHandler()
    handler._add_to_queue("/fake/test.stl", "test.stl")  # pylint: disable=protected-access

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()


@patch("src.watchdog.main.SessionLocal")
def test_add_to_queue_exception_handling(mock_session_local):
    """Verify add_to_queue rolls back the transaction on exception."""
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    # Simulate DB query raising an exception
    mock_db.query.side_effect = Exception("DB Connection Error")

    handler = PrintQueueEventHandler()
    handler._add_to_queue("/fake/test.stl", "test.stl")  # pylint: disable=protected-access

    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()


@patch("src.watchdog.main.time.sleep", side_effect=KeyboardInterrupt)
@patch("src.watchdog.main.Observer")
@patch("src.watchdog.main.Base.metadata.create_all")
def test_main_watchdog_loop(mock_create_all, mock_observer_class, mock_sleep):
    """Verify the main loop starts and stops the observer correctly."""
    mock_observer = MagicMock()
    mock_observer_class.return_value = mock_observer

    main()

    mock_create_all.assert_called_once()
    mock_observer.start.assert_called_once()
    mock_observer.stop.assert_called_once()
    mock_observer.join.assert_called_once()
