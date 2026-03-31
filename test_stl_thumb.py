import trimesh
from PIL import Image
import numpy as np

def render_fallback(file_path: str, output_path: str):
    mesh = trimesh.load(file_path)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)

    # Very basic rendering fallback: using trimesh.Scene.save_image which requires some backend (pyglet usually)
    # However since we're headless, it might be tricky. Let's see if pyglet headless works.
    scene = trimesh.Scene(mesh)
    try:
        png = scene.save_image(resolution=[400, 400])
        with open(output_path, 'wb') as f:
            f.write(png)
        print("Trimesh rendering successful!")
    except Exception as e:
        print(f"Trimesh rendering failed: {e}")
