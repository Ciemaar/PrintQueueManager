import trimesh
import os
def render_fallback(file_path: str, output_path: str):
    os.system("Xvfb :99 -screen 0 1024x768x24 &")
    os.environ['DISPLAY'] = ':99'
    mesh = trimesh.load(file_path)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    scene = trimesh.Scene(mesh)
    try:
        png = scene.save_image(resolution=[400, 400])
        with open(output_path, 'wb') as f:
            f.write(png)
        print("Trimesh rendering successful!")
    except Exception as e:
        print(f"Trimesh rendering failed: {e}")
