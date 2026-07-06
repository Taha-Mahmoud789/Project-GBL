"""Test VectorEngine against real SVGs in test-svgs/ — skip huge files."""
import sys
sys.path.insert(0, ".")
import os
import traceback
from engines.vector_engine import VectorEngine

engine = VectorEngine()
test_dir = os.path.join(os.path.dirname(__file__), "..", "test-svgs")

results = []
for fname in sorted(os.listdir(test_dir)):
    if not fname.endswith(".svg"):
        continue
    # Skip the huge auto-generated SVGs
    if "export" in fname:
        print(f"  SKIP {fname}: too large")
        results.append((fname, "SKIP", 0))
        continue
    path = os.path.join(test_dir, fname)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()
    try:
        scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
        n_meshes = len(scene.geometry)
        results.append((fname, "OK", n_meshes))
        print(f"  OK  {fname}: {n_meshes} meshes")
    except Exception as e:
        results.append((fname, f"FAIL: {e}", 0))
        print(f"  FAIL {fname}: {e}")
        traceback.print_exc()

print(f"\n{'='*60}")
ok = sum(1 for _, s, _ in results if s == "OK")
total = len(results)
print(f"Results: {ok}/{total} passed (excluding skipped)")
for fname, status, n in results:
    if status == "SKIP":
        print(f"  [SKIP] {fname}")
    elif status == "OK":
        print(f"  [OK]   {fname}: {n} meshes")
    else:
        print(f"  [FAIL] {fname}: {status}")
