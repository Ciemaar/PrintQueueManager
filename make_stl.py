import trimesh
mesh = trimesh.creation.box(extents=[1, 1, 1])
mesh.export('test.stl')
