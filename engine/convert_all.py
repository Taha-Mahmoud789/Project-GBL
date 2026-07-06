"""Convert all test SVGs to GLB files with visible output."""
import os
import sys
import time
import trimesh

sys.path.insert(0, os.path.dirname(__file__))

from engines.vector_engine import VectorEngine
from engines.layer_engine import LayerEngine
from engines.raster_engine import RasterEngine
from exporters.glb_exporter import export_glb

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "test-svgs")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_3d")

settings = {
    "depth": 0.5,
    "bevel": 0.0,
    "smoothness": 5,
    "material": {"color": "#6366f1", "metalness": 0.2, "roughness": 0.3},
}

svg_files = sorted([f for f in os.listdir(TEST_DIR) if f.endswith(".svg") and "export" not in f])

print("=" * 60)
print("  SVG TO 3D CONVERTER")
print("  %d SVG files to convert" % len(svg_files))
print("  Output: engine/output_3d/")
print("=" * 60)

for i, fname in enumerate(svg_files, 1):
    svg_path = os.path.join(TEST_DIR, fname)
    out_name = os.path.splitext(fname)[0] + ".glb"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    with open(svg_path, "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()

    print("\n[%d/%d] %s" % (i, len(svg_files), fname))
    print("-" * 40)

    engines = [
        ("VectorEngine", VectorEngine()),
        ("LayerEngine", LayerEngine()),
        ("RasterEngine", RasterEngine()),
    ]

    for eng_name, engine in engines:
        t0 = time.time()
        try:
            scene = engine.convert(svg, settings)
            n = len(scene.geometry)
            elapsed = time.time() - t0
            print("  %s: %d meshes in %.2fs" % (eng_name, n, elapsed))
        except Exception as e:
            elapsed = time.time() - t0
            print("  %s: ERROR %s in %.2fs" % (eng_name, e, elapsed))

    # Export best result using VectorEngine (fallback to RasterEngine)
    t0 = time.time()
    scene = VectorEngine().convert(svg, settings)
    if len(scene.geometry) == 0:
        scene = RasterEngine().convert(svg, settings)

    if len(scene.geometry) > 0:
        glb = export_glb(scene)
        with open(out_path, "wb") as f:
            f.write(glb)
        elapsed = time.time() - t0
        print("  >>> SAVED: %s (%d bytes)" % (out_name, len(glb)))
    else:
        print("  >>> SKIPPED (no geometry)")

print("\n" + "=" * 60)
print("  DONE! All files in engine/output_3d/")
print("=" * 60)
