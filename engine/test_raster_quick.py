import sys, time; sys.path.insert(0, '.')
from engines.raster_engine import RasterEngine

engine = RasterEngine()

svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect x="10" y="10" width="30" height="30" fill="#ff0000"/>
<circle cx="70" cy="70" r="20" fill="#00ff00"/>
</svg>"""

t0 = time.time()
scene = engine.convert(svg, {"depth": 0.5, "render_size": 256})
elapsed = time.time() - t0
print(f"Simple SVG: {len(scene.geometry)} meshes in {elapsed:.2f}s")

# Now test with a complex SVG (wordpress has no base64 images)
with open("../test-svgs/wordpress-plain.svg", "r", encoding="utf-8", errors="replace") as f:
    svg2 = f.read()
t0 = time.time()
scene2 = engine.convert(svg2, {"depth": 0.5, "render_size": 256})
elapsed = time.time() - t0
print(f"wordpress: {len(scene2.geometry)} meshes in {elapsed:.2f}s")

# Test with html5 (no masks/filters, just paths)
with open("../test-svgs/html5-original-wordmark.svg", "r", encoding="utf-8", errors="replace") as f:
    svg3 = f.read()
t0 = time.time()
scene3 = engine.convert(svg3, {"depth": 0.5, "render_size": 256})
elapsed = time.time() - t0
print(f"html5: {len(scene3.geometry)} meshes in {elapsed:.2f}s")
