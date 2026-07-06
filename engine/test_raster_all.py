import sys, time, traceback; sys.path.insert(0, '.')
from engines.raster_engine import RasterEngine

engine = RasterEngine()

# Test all 13 SVGs
import os
test_dir = os.path.join(os.path.dirname(__file__), "..", "test-svgs")
results = []
for fname in sorted(os.listdir(test_dir)):
    if not fname.endswith(".svg"):
        continue
    if "export" in fname:
        continue  # skip huge auto-generated
    with open(os.path.join(test_dir, fname), "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()
    t0 = time.time()
    try:
        scene = engine.convert(svg, {"depth": 0.5, "render_size": 512})
        elapsed = time.time() - t0
        n = len(scene.geometry)
        results.append((fname, "OK", n, elapsed))
        print(f"  OK  {fname}: {n} meshes in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - t0
        results.append((fname, f"FAIL: {e}", 0, elapsed))
        print(f"  FAIL {fname}: {e} in {elapsed:.2f}s")

ok = sum(1 for _, s, _, _ in results if s == "OK")
print(f"\n{ok}/{len(results)} passed")
