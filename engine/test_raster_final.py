import sys, time, os; sys.path.insert(0, '.')
from engines.raster_engine import RasterEngine

engine = RasterEngine()
test_dir = os.path.join(os.path.dirname(__file__), "..", "test-svgs")

for fname in sorted(os.listdir(test_dir)):
    if not fname.endswith(".svg") or "export" in fname:
        continue
    with open(os.path.join(test_dir, fname), "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()
    t0 = time.time()
    scene = engine.convert(svg, {"depth": 0.5, "render_size": 256})
    elapsed = time.time() - t0
    print(f"{'OK' if len(scene.geometry)>0 else 'EMPTY':6s} {fname}: {len(scene.geometry)} meshes in {elapsed:.2f}s")
