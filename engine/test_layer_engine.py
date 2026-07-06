"""Test LayerEngine against test SVGs."""
import sys, os, time, traceback
sys.path.insert(0, ".")
from engines.layer_engine import LayerEngine

engine = LayerEngine()
test_dir = os.path.join(os.path.dirname(__file__), "..", "test-svgs")

svgs = [
    "react-original.svg",
    "javascript-plain.svg",
    "tailwindcss-original.svg",
    "php-original.svg",
    "css3-original-wordmark.svg",
    "html5-original-wordmark.svg",
    "woocommerce-original.svg",
]

for fname in svgs:
    path = os.path.join(test_dir, fname)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()
    t0 = time.time()
    try:
        scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
        elapsed = time.time() - t0
        n_meshes = len(scene.geometry)
        # Also test layer metadata
        layers = engine.convert_to_layers(svg, {"depth": 0.5})
        print(f"OK   {fname}: {n_meshes} meshes, {len(layers)} layers in {elapsed:.2f}s")
        for l in layers:
            print(f"       {l['name']}: color={l['color']}, meshes={l['meshCount']}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAIL {fname}: {e} in {elapsed:.2f}s")
        traceback.print_exc()

print("\n=== LayerEngine tests done ===")
