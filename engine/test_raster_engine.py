"""Test RasterEngine against complex SVGs."""
import sys, os, time, traceback
sys.path.insert(0, ".")
from engines.raster_engine import RasterEngine

engine = RasterEngine()
test_dir = os.path.join(os.path.dirname(__file__), "..", "test-svgs")

# Focus on SVGs with masks, clipPaths, filters, embedded images
svgs = [
    "GeekCode.svg",
    "bootstrap-original-wordmark.svg",
    "jquery-plain-wordmark.svg",
    "wordpress-plain.svg",
]

for fname in svgs:
    path = os.path.join(test_dir, fname)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()
    t0 = time.time()
    try:
        scene = engine.convert(svg, {
            "depth": 0.5,
            "material": {"color": "#6366f1"},
            "render_size": 512,
        })
        elapsed = time.time() - t0
        print(f"OK   {fname}: {len(scene.geometry)} meshes in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAIL {fname}: {e} in {elapsed:.2f}s")
        traceback.print_exc()

print("\n=== RasterEngine tests done ===")
