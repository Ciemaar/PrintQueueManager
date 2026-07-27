from unittest.mock import MagicMock, patch

from src.worker.thumbnail_generator import (
    generate_thumbnail,
    get_thumbnail_file_path,
    get_thumbnail_path,
)


def test_get_thumbnail_file_path():
    """Test absolute path generation for a job ID."""
    path = get_thumbnail_file_path(123)
    assert "static/thumbnails/job_123.png" in path.replace("\\", "/")


@patch("src.worker.thumbnail_generator.os.path.exists")
def test_get_thumbnail_path(mock_exists):
    """Test relative URL path generation based on file existence."""
    mock_exists.return_value = True
    path = get_thumbnail_path(123)
    assert path == "/static/thumbnails/job_123.png"

    mock_exists.return_value = False
    path = get_thumbnail_path(123)
    assert path is None


@patch("src.worker.thumbnail_generator.os.path.exists")
@patch("src.worker.thumbnail_generator.trimesh.load")
@patch("src.worker.thumbnail_generator.trimesh.Scene")
@patch("builtins.open", new_callable=MagicMock)
def test_generate_thumbnail_success(mock_open, mock_scene_cls, mock_load, mock_exists):
    """Test successful thumbnail generation with mocked 3D rendering."""
    mock_exists.return_value = True
    mock_scene = MagicMock()
    mock_scene.save_image.return_value = b"fake_png_data"
    mock_scene_cls.return_value = mock_scene

    result = generate_thumbnail("test.stl", 123)

    assert result is True
    mock_load.assert_called_once_with("test.stl", force="mesh")
    mock_scene.save_image.assert_called_once()
    mock_open.assert_called_once()


@patch("src.worker.thumbnail_generator.os.path.exists")
def test_generate_thumbnail_failure(mock_exists):
    """Test graceful failure when file is missing."""
    mock_exists.return_value = False
    result = generate_thumbnail("missing.stl", 123)
    assert result is False
