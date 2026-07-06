"""Quick debug of vector engine path parsing."""
import sys
sys.path.insert(0, "C:\\Users\\tabdo\\Desktop\\Project-GBL\\image2model\\apps\\web\\engine")

from engines.vector_engine import _path_to_polygons, _apply_matrix, _el_to_polygons
from lxml import etree
import numpy as np

# Test with tailwind SVG
svg = open("C:\\Users\\tabdo\\Desktop\\Project-GBL\\image2model\\apps\\web\\test-svgs\\tailwindcss-original.svg", "r").read()
root = etree.fromstring(svg.encode("utf-8"))

NS_SVG = "http://www.w3.org/2000/svg"
for el in root.iter(f"{{{NS_SVG}}}path"):
    d = el.get("d", "")
    polys = _path_to_polygons(d)
    for i, p in enumerate(polys):
        print(f"  Path {i}: {len(p)} points, closed={np.allclose(p[0], p[-1])}")
        if len(p) < 4:
            print(f"    TOO FEW POINTS: {p}")
