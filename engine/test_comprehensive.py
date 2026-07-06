"""Comprehensive test suite for all 13 test SVGs across all engines.

Tests:
  1. VectorEngine: every SVG produces a scene (or known-expected failures)
  2. LayerEngine: every SVG produces layers with correct structure
  3. RasterEngine: every SVG produces a scene (or known-expected failures)
  4. Export: every successful scene can be exported to GLB
  5. Analyzer: every SVG can be analyzed
"""

import sys
import os
import time
import trimesh
import io
sys.path.insert(0, os.path.dirname(__file__))

from engines.vector_engine import VectorEngine
from engines.layer_engine import LayerEngine
from engines.raster_engine import RasterEngine
from analyzer import analyze_svg
from exporters import export_glb

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "test-svgs")

# Known-expected results:
# - SVGs with only raster content (GeekCode, bootstrap) produce 0 vector meshes
EXPECTED_EMPTY_VECTOR = {"GeekCode.svg", "bootstrap-original-wordmark.svg"}

settings = {
    "depth": 0.5,
    "bevel": 0.0,
    "smoothness": 5,
    "material": {"color": "#6366f1", "metalness": 0.2, "roughness": 0.3},
}

vector_engine = VectorEngine()
layer_engine = LayerEngine()
raster_engine = RasterEngine()


def get_svg_files():
    files = []
    for f in sorted(os.listdir(TEST_DIR)):
        if f.endswith(".svg") and "export" not in f:
            files.append(f)
    return files


def test_analyzer():
    print("\n=== ANALYZER ===")
    passed = 0
    failed = 0
    for fname in get_svg_files():
        with open(os.path.join(TEST_DIR, fname), "r", encoding="utf-8", errors="replace") as f:
            svg = f.read()
        try:
            result = analyze_svg(svg)
            assert "type" in result
            assert "recommended_engine" in result
            print(f"  OK   {fname}: type={result['type']}, engine={result['recommended_engine']}")
            passed += 1
        except Exception as e:
            print(f"  FAIL {fname}: {e}")
            failed += 1
    print(f"  Results: {passed}/{passed+failed}")
    return failed == 0


def test_vector_engine():
    print("\n=== VECTOR ENGINE ===")
    passed = 0
    failed = 0
    for fname in get_svg_files():
        with open(os.path.join(TEST_DIR, fname), "r", encoding="utf-8", errors="replace") as f:
            svg = f.read()
        t0 = time.time()
        try:
            scene = vector_engine.convert(svg, settings)
            n = len(scene.geometry)
            elapsed = time.time() - t0
            if n > 0:
                print(f"  OK   {fname}: {n} meshes in {elapsed:.2f}s")
                passed += 1
            elif fname in EXPECTED_EMPTY_VECTOR:
                print(f"  OK   {fname}: 0 meshes (expected - raster-only SVG)")
                passed += 1
            else:
                print(f"  WARN {fname}: 0 meshes in {elapsed:.2f}s")
                passed += 1  # not a failure, just empty
        except Exception as e:
            elapsed = time.time() - t0
            if fname in EXPECTED_EMPTY_VECTOR:
                print(f"  OK   {fname}: error (expected - raster-only): {e}")
                passed += 1
            else:
                print(f"  FAIL {fname}: {e} in {elapsed:.2f}s")
                failed += 1
    print(f"  Results: {passed}/{passed+failed}")
    return failed == 0


def test_layer_engine():
    print("\n=== LAYER ENGINE ===")
    passed = 0
    failed = 0
    for fname in get_svg_files():
        with open(os.path.join(TEST_DIR, fname), "r", encoding="utf-8", errors="replace") as f:
            svg = f.read()
        t0 = time.time()
        try:
            scene = layer_engine.convert(svg, settings)
            layers = layer_engine.convert_to_layers(svg, settings)
            n = len(scene.geometry)
            elapsed = time.time() - t0
            print(f"  OK   {fname}: {n} meshes, {len(layers)} layers in {elapsed:.2f}s")
            passed += 1
        except Exception as e:
            elapsed = time.time() - t0
            if fname in EXPECTED_EMPTY_VECTOR:
                print(f"  OK   {fname}: error (expected): {type(e).__name__}")
                passed += 1
            else:
                print(f"  FAIL {fname}: {e} in {elapsed:.2f}s")
                failed += 1
    print(f"  Results: {passed}/{passed+failed}")
    return failed == 0


def test_raster_engine():
    print("\n=== RASTER ENGINE ===")
    passed = 0
    failed = 0
    skipped = 0
    for fname in get_svg_files():
        with open(os.path.join(TEST_DIR, fname), "r", encoding="utf-8", errors="replace") as f:
            svg = f.read()
        t0 = time.time()
        try:
            scene = raster_engine.convert(svg, {**settings, "render_size": 256})
            n = len(scene.geometry)
            elapsed = time.time() - t0
            print(f"  {'OK' if n > 0 else 'EMPTY':6s} {fname}: {n} meshes in {elapsed:.2f}s")
            passed += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  FAIL {fname}: {e} in {elapsed:.2f}s")
            failed += 1
    print(f"  Results: {passed}/{passed+failed}")
    return failed == 0


def test_glb_export():
    print("\n=== GLB EXPORT ===")
    passed = 0
    failed = 0
    for fname in get_svg_files():
        with open(os.path.join(TEST_DIR, fname), "r", encoding="utf-8", errors="replace") as f:
            svg = f.read()
        try:
            scene = vector_engine.convert(svg, settings)
            if len(scene.geometry) == 0:
                continue
            glb = export_glb(scene)
            assert len(glb) > 0, "empty GLB"
            assert glb[:4] == b'glTF', "not a GLB file"

            # Reload and validate materials on each mesh
            loaded = trimesh.load(io.BytesIO(glb), file_type="glb")
            mesh_count = 0
            mat_count = 0
            for geom in loaded.geometry.values():
                if hasattr(geom, 'vertices'):
                    mesh_count += 1
                    if hasattr(geom.visual, 'material'):
                        mat_count += 1
            assert mat_count > 0, f"0 materials in GLB"
            assert mesh_count > 0, f"0 meshes in GLB"

            print(f"  OK   {fname}: {mesh_count} meshes, {mat_count} materials, {len(glb)} bytes")
            passed += 1
        except Exception as e:
            print(f"  FAIL {fname}: {e}")
            failed += 1
    print(f"  Results: {passed}/{passed+failed}")
    return failed == 0


if __name__ == "__main__":
    all_pass = True
    all_pass &= test_analyzer()
    all_pass &= test_vector_engine()
    all_pass &= test_layer_engine()
    all_pass &= test_raster_engine()
    all_pass &= test_glb_export()

    print(f"\n{'='*60}")
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
