from pathlib import Path
from unittest.mock import MagicMock, patch

from src.worker.thumbnail_generator import (
    generate_thumbnail,
    get_thumbnail_file_path,
    get_thumbnail_path,
)


def test_get_thumbnail_path():
    """Verify the expected web path for a given file thumbnail."""
    path = get_thumbnail_path(Path("/test/file.stl"))
    assert str(path).replace("\\", "/").startswith("/static/thumbnails/")
    assert str(path).replace("\\", "/").endswith(".png")


def test_get_thumbnail_file_path():
    """Verify the expected local file path for a thumbnail."""
    path = get_thumbnail_file_path(Path("/test/file.stl"))
    assert isinstance(path, Path)
    assert path.name.endswith(".png")


@patch("src.worker.thumbnail_generator.trimesh.load")
@patch("src.worker.thumbnail_generator.trimesh.Scene", autospec=True)
@patch("builtins.open")
def test_generate_thumbnail_success(mock_open, mock_scene_cls, mock_load):
    """Test generating a thumbnail successfully from a mocked mesh."""

    class DummyMesh:
        pass

    mock_mesh = DummyMesh()
    mock_load.return_value = mock_mesh

    mock_scene = MagicMock()
    mock_scene.save_image.return_value = b"image_data"
    mock_scene_cls.return_value = mock_scene

    result = generate_thumbnail(Path("/test/file.stl"), Path("out.png"))

    assert result is True
    mock_load.assert_called_once_with(str(Path("/test/file.stl")))
    mock_scene.save_image.assert_called_once()
    mock_open.assert_called_once_with(Path("out.png"), "wb")


@patch("src.worker.thumbnail_generator.trimesh.load")
def test_generate_thumbnail_failure(mock_load):
    """Test thumbnail generation gracefully handles exceptions."""
    mock_load.side_effect = Exception("Load failed")

    result = generate_thumbnail(Path("/test/file.stl"), Path("out.png"))

    assert result is False
    mock_load.assert_called_once_with(str(Path("/test/file.stl")))
