"""Debug trimesh extrusion."""
import sys
sys.path.insert(0, ".")
import trimesh
from shapely.geometry import Polygon
import numpy as np

poly = Polygon([(10, 10), (40, 10), (40, 40), (10, 40), (10, 10)])
print(f"Polygon valid={poly.is_valid} empty={poly.is_empty} area={poly.area}")

try:
    mesh = trimesh.creation.extrude_polygon(poly, height=0.5, engine="triangle")
    print(f"triangle engine: {mesh}")
    if mesh:
        print(f"  verts={len(mesh.vertices)} faces={len(mesh.faces)}")
except Exception as e:
    print(f"triangle engine FAILED: {e}")

try:
    mesh = trimesh.creation.extrude_polygon(poly, height=0.5)
    print(f"default engine: {mesh}")
    if mesh:
        print(f"  verts={len(mesh.vertices)} faces={len(mesh.faces)}")
except Exception as e:
    print(f"default engine FAILED: {e}")

# Try without closing the polygon
poly2 = Polygon([(10, 10), (40, 10), (40, 40), (10, 40)])
print(f"\nPolygon2 valid={poly2.is_valid} area={poly2.area}")
try:
    mesh = trimesh.creation.extrude_polygon(poly2, height=0.5)
    print(f"mesh2: {mesh}")
    if mesh:
        print(f"  verts={len(mesh.vertices)} faces={len(mesh.faces)}")
except Exception as e:
    print(f"mesh2 FAILED: {e}")
