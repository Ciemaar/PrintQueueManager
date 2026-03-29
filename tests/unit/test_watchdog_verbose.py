from unittest.mock import MagicMock, patch
from src.watchdog.main import PrintQueueEventHandler
from src.app.config import settings


def test_on_created_verbose_logging_valid_file(capsys):
    """Test verbose logging for a valid 3D file."""
    # Ensure verbose is ON for this test
    original_verbose = settings.verbose
    settings.verbose = True

    try:
        handler = PrintQueueEventHandler()
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.event_type = "created"
        mock_event.src_path = "/test/model.STL"  # Note the capital STL

        with patch.object(handler, "_add_to_queue"):
            handler.on_created(mock_event)

            captured = capsys.readouterr()
            assert "[VERBOSE] Watchdog event received" in captured.out
            assert "[VERBOSE] Detected valid 3D file: model.STL" in captured.out
    finally:
        settings.verbose = original_verbose


def test_on_created_verbose_logging_invalid_file(capsys):
    """Test verbose logging ignoring non-3D files."""
    original_verbose = settings.verbose
    settings.verbose = True

    try:
        handler = PrintQueueEventHandler()
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.event_type = "created"
        mock_event.src_path = "/test/document.txt"

        with patch.object(handler, "_add_to_queue") as mock_add:
            handler.on_created(mock_event)

            captured = capsys.readouterr()
            assert "[VERBOSE] Ignored non-3D file: document.txt" in captured.out
            mock_add.assert_not_called()
    finally:
        settings.verbose = original_verbose


def test_on_created_verbose_logging_directory(capsys):
    """Test verbose logging ignoring directory creation."""
    original_verbose = settings.verbose
    settings.verbose = True

    try:
        handler = PrintQueueEventHandler()
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.event_type = "created"
        mock_event.src_path = "/test/new_folder"

        handler.on_created(mock_event)

        captured = capsys.readouterr()
        assert "[VERBOSE] Ignored directory creation: /test/new_folder" in captured.out
    finally:
        settings.verbose = original_verbose
