import sys, time, os; sys.path.insert(0, '.')
from engines.raster_engine import RasterEngine

engine = RasterEngine()
fname = sys.argv[1]
with open(f"../test-svgs/{fname}", "r", encoding="utf-8", errors="replace") as f:
    svg = f.read()
t0 = time.time()
scene = engine.convert(svg, {"depth": 0.5, "render_size": 256})
elapsed = time.time() - t0
print(f"{fname}: {len(scene.geometry)} meshes in {elapsed:.2f}s")
