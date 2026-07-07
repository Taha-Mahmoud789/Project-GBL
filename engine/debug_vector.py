"""Debug VectorEngine."""
import sys
sys.path.insert(0, ".")

from geometry import parse_svg, normalize
from engines.vector_engine import VectorEngine

svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="10" y="10" width="30" height="30" fill="#ff0000"/></svg>'

doc = parse_svg(svg)
print(f"viewBox: {doc.viewBox}")
print(f"shapes: {len(doc.shapes)}")
for s in doc.shapes:
    print(f"  tag={s.tag} fill={s.fill} attrs={s.attributes}")

shapes = normalize(doc, target_width=100, target_height=100)
print(f"\nnormalized: {len(shapes)}")
for s in shapes:
    print(f"  id={s.id} fill={s.fill} polys={len(s.polygons)} bbox={s.bbox}")
    for i, p in enumerate(s.polygons):
        print(f"    poly {i}: {p.shape} pts={p[:3]}...")

# Now try extrusion
from engines.vector_engine import _extrude_polygon, _build_shapely_polygon
from shapely.geometry import Polygon

if shapes:
    polys = shapes[0].polygons
    print(f"\nTrying to build Shapely polygon from {len(polys)} polys")
    for i, p in enumerate(polys):
        print(f"  pts shape: {p.shape}, first 3: {p[:3]}")
        try:
            poly = Polygon(p)
            print(f"  valid={poly.is_valid} empty={poly.is_empty} area={poly.area}")
        except Exception as e:
            print(f"  ERROR: {e}")

    compound = _build_shapely_polygon(polys)
    if compound:
        print(f"\nCompound polygon: valid={compound.is_valid} empty={compound.is_empty} area={compound.area}")
        mesh = _extrude_polygon(compound, 0.5, "#ff0000", 0.2, 0.3)
        if mesh:
            print(f"Mesh: verts={len(mesh.vertices)} faces={len(mesh.faces)}")
        else:
            print("Mesh: None")
    else:
        print("Compound polygon: None")

engine = VectorEngine()
scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
print(f"\nScene geometry count: {len(scene.geometry)}")
