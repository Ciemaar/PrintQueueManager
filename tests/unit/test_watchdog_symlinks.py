import logging
from unittest.mock import MagicMock, patch

from src.app.config import settings
from src.watchdog.main import PrintQueueEventHandler


def test_on_created_symlink_valid(caplog, tmp_path):
    """Test that valid symlinks are handled correctly by the watchdog."""
    # Ensure verbose is ON for this test
    original_verbose = settings.verbose
    settings.verbose = True

    # Create an actual physical file and a symlink to it
    target_file = tmp_path / "real_file.stl"
    target_file.write_text("dummy")

    symlink_file = tmp_path / "link.stl"
    symlink_file.symlink_to(target_file)

    try:
        handler = PrintQueueEventHandler()
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.event_type = "created"
        mock_event.src_path = str(symlink_file)

        with patch.object(handler, "_add_to_queue") as mock_add:
            with caplog.at_level(logging.DEBUG):
                handler.on_created(mock_event)

                assert "Detected valid 3D file: link.stl" in caplog.text
                mock_add.assert_called_once_with(str(symlink_file), "link.stl", False)
    finally:
        settings.verbose = original_verbose


def test_on_created_symlink_broken(caplog, tmp_path):
    """Test that broken symlinks are ignored by the watchdog."""
    original_verbose = settings.verbose
    settings.verbose = True

    broken_symlink = tmp_path / "broken.stl"
    broken_symlink.symlink_to(tmp_path / "does_not_exist.stl")

    try:
        handler = PrintQueueEventHandler()
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.event_type = "created"
        mock_event.src_path = str(broken_symlink)

        with patch.object(handler, "_add_to_queue") as mock_add:
            with caplog.at_level(logging.DEBUG):
                handler.on_created(mock_event)

                assert "Detected broken symlink: broken.stl" in caplog.text
                mock_add.assert_called_once_with(str(broken_symlink), "broken.stl", True)
    finally:
        settings.verbose = original_verbose
