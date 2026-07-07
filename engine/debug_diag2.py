import sys; sys.path.insert(0, '.')
from geometry import parse_svg, normalize
from geometry.normalizer import _path_to_polygons

svg = open('../test-svgs/wordpress-plain.svg').read()
svg2 = open('../test-svgs/javascript-plain.svg').read()

# For wordpress, check the raw polygon data
doc = parse_svg(svg)
shapes = normalize(doc, target_width=100.0)
print(f'wordpress normalized shapes: {len(shapes)}')
for s in shapes[:5]:
    for p in s.polygons:
        print(f'  shape "{s.id}": {len(p)} points, bbox_x=[{p[:,0].min():.1f}, {p[:,0].max():.1f}], bbox_y=[{p[:,1].min():.1f}, {p[:,1].max():.1f}]')

# For javascript
doc2 = parse_svg(svg2)
shapes2 = normalize(doc2, target_width=100.0)
print(f'\njavascript normalized shapes: {len(shapes2)}')
for s in shapes2:
    for p in s.polygons:
        print(f'  shape "{s.id}": {len(p)} points, bbox_x=[{p[:,0].min():.1f}, {p[:,0].max():.1f}], bbox_y=[{p[:,1].min():.1f}, {p[:,1].max():.1f}]')
