import trimesh
import pyrender
import numpy as np
from PIL import Image

def generate_thumbnail(file_path: str, output_path: str):
    mesh = trimesh.load(file_path)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)

    mesh_pyrender = pyrender.Mesh.from_trimesh(mesh)
    scene = pyrender.Scene(ambient_light=[0.2, 0.2, 0.2])
    scene.add(mesh_pyrender)

    # Camera
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=1.0)
    # Positioning the camera based on bounding box
    bounds = mesh.bounds
    center = np.mean(bounds, axis=0)
    extents = bounds[1] - bounds[0]
    distance = np.max(extents) * 1.5

    camera_pose = np.eye(4)
    camera_pose[:3, 3] = center + np.array([0, 0, distance])
    scene.add(camera, pose=camera_pose)

    # Light
    light = pyrender.DirectionalLight(color=np.ones(3), intensity=2.0)
    scene.add(light, pose=camera_pose)

    # Render
    # Setting offscreen renderer requires PyOpenGL, which in headless environments might need osmesa or egl.
    r = pyrender.OffscreenRenderer(400, 400)
    color, depth = r.render(scene)

    img = Image.fromarray(color)
    img.save(output_path)

print("Libraries imported successfully")
