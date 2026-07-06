"""Smoke test for VectorEngine with new geometry module."""
import sys
sys.path.insert(0, ".")

from engines.vector_engine import VectorEngine

def test_vector_engine_simple():
    engine = VectorEngine()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="10" y="10" width="30" height="30" fill="#ff0000"/></svg>'
    scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1", "metalness": 0.2, "roughness": 0.3}})
    assert len(scene.geometry) > 0, "scene should have geometry"
    print(f"test_vector_engine_simple PASSED ({len(scene.geometry)} meshes)")

def test_vector_engine_multi_color():
    engine = VectorEngine()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="0" y="0" width="50" height="50" fill="#ff0000"/><rect x="50" y="50" width="50" height="50" fill="#00ff00"/></svg>'
    scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
    assert len(scene.geometry) >= 2, f"expected >= 2 meshes, got {len(scene.geometry)}"
    print(f"test_vector_engine_multi_color PASSED ({len(scene.geometry)} meshes)")

def test_vector_engine_viewbox():
    engine = VectorEngine()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="100" height="100"><circle cx="250" cy="250" r="100" fill="#6366f1"/></svg>'
    scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
    assert len(scene.geometry) > 0
    print(f"test_vector_engine_viewbox PASSED ({len(scene.geometry)} meshes)")

def test_vector_engine_compound_path():
    engine = VectorEngine()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M10 10 L90 10 L90 90 L10 90 Z M30 30 L70 30 L70 70 L30 70 Z" fill="#ff0000"/></svg>'
    scene = engine.convert(svg, {"depth": 0.5, "material": {"color": "#6366f1"}})
    assert len(scene.geometry) > 0
    print(f"test_vector_engine_compound_path PASSED ({len(scene.geometry)} meshes)")

def test_vector_engine_to_layers():
    engine = VectorEngine()
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g id="bg"><rect x="0" y="0" width="100" height="100" fill="#ff0000"/></g><g id="fg"><circle cx="50" cy="50" r="20" fill="#00ff00"/></g></svg>'
    layers = engine.convert_to_layers(svg, {"depth": 0.5})
    assert len(layers) >= 1, f"expected >= 1 layers, got {len(layers)}"
    print(f"test_vector_engine_to_layers PASSED ({len(layers)} layers)")

if __name__ == "__main__":
    test_vector_engine_simple()
    test_vector_engine_multi_color()
    test_vector_engine_viewbox()
    test_vector_engine_compound_path()
    test_vector_engine_to_layers()
    print("\n=== ALL VECTOR ENGINE TESTS PASSED ===")
