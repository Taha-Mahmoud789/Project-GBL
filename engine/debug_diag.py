import sys; sys.path.insert(0, '.')
from engines.vector_engine import VectorEngine
from exporters.glb_exporter import export_glb
import trimesh, numpy as np

svg = open('../test-svgs/wordpress-plain.svg').read()
scene = VectorEngine().convert(svg, {'depth': 0.5, 'material': {'color': '#6366f1', 'metalness': 0.2, 'roughness': 0.3}})
print(f'wordpress meshes: {len(scene.geometry)}')
for name, geom in scene.geometry.items():
    if hasattr(geom, 'vertices'):
        bb = geom.bounding_box.extents
        print(f'  {name}: verts={len(geom.vertices)}, bbox_extents={bb}')

# Test 2: javascript-plain.svg
svg2 = open('../test-svgs/javascript-plain.svg').read()
scene2 = VectorEngine().convert(svg2, {'depth': 0.5, 'material': {'color': '#6366f1', 'metalness': 0.2, 'roughness': 0.3}})
print(f'\njavascript meshes: {len(scene2.geometry)}')
for name, geom in scene2.geometry.items():
    if hasattr(geom, 'vertices'):
        bb = geom.bounding_box.extents
        print(f'  {name}: verts={len(geom.vertices)}, bbox_extents={bb}')

# Test 3: Check the normalized polygons BEFORE extrusion
from geometry import parse_svg, normalize
from geometry.normalizer import _path_to_polygons

# For wordpress, check the raw polygon data
doc = parse_svg(svg)
shapes = normalize(doc, target_size=100.0)
print(f'\nwordpress normalized shapes: {len(shapes)}')
for s in shapes[:5]:
    for p in s.polygons:
        print(f'  shape "{s.id}": {len(p)} points, bbox_x=[{p[:,0].min():.1f}, {p[:,0].max():.1f}], bbox_y=[{p[:,1].min():.1f}, {p[:,1].max():.1f}]')

# For javascript
doc2 = parse_svg(svg2)
shapes2 = normalize(doc2, target_size=100.0)
print(f'\njavascript normalized shapes: {len(shapes2)}')
for s in shapes2:
    for p in s.polygons:
        print(f'  shape "{s.id}": {len(p)} points, bbox_x=[{p[:,0].min():.1f}, {p[:,0].max():.1f}], bbox_y=[{p[:,1].min():.1f}, {p[:,1].max():.1f}]')
