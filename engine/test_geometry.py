"""Quick smoke test for the geometry module."""
from geometry import parse_svg, normalize, extract_layers
from geometry.transforms import parse_transform, build_viewbox_matrix, apply_matrix, compose_chain
import numpy as np

def test_parse_simple():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><g fill="#61DAFB"><circle cx="64" cy="64" r="11.4"/><path d="M10 10 L50 10 L50 50 L10 50 Z"/></g></svg>'
    doc = parse_svg(svg)
    assert doc.viewBox == (0, 0, 128, 128), f"viewBox wrong: {doc.viewBox}"
    assert len(doc.shapes) == 2, f"expected 2 shapes, got {len(doc.shapes)}"
    assert doc.shapes[0].tag == "circle"
    assert doc.shapes[1].tag == "path"
    print("test_parse_simple PASSED")

def test_normalize():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="10" y="10" width="30" height="30" fill="#ff0000"/><rect x="60" y="60" width="30" height="30" fill="#00ff00"/></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc, target_width=200, target_height=200)
    assert len(shapes) == 2, f"expected 2, got {len(shapes)}"
    # Both rects should have bounding boxes
    for s in shapes:
        assert s.bbox[2] > s.bbox[0], "bbox width should be > 0"
        assert s.bbox[3] > s.bbox[1], "bbox height should be > 0"
    print("test_normalize PASSED")

def test_layers():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g id="group1" fill="#ff0000"><rect x="0" y="0" width="50" height="50"/></g><g id="group2" fill="#00ff00"><rect x="50" y="50" width="50" height="50"/></g></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc)
    layers = extract_layers(shapes, mode="auto")
    assert len(layers) == 2, f"expected 2 layers, got {len(layers)}"
    print("test_layers PASSED")

def test_flat_mode():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g fill="#ff0000"><rect x="0" y="0" width="50" height="50"/><rect x="50" y="50" width="50" height="50"/></g></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc)
    layers = extract_layers(shapes, mode="flat")
    assert len(layers) == 1, f"expected 1, got {len(layers)}"
    assert len(layers[0].shapes) == 2
    print("test_flat_mode PASSED")

def test_color_mode():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="0" y="0" width="50" height="50" fill="#ff0000"/><rect x="50" y="0" width="50" height="50" fill="#ff0000"/><rect x="0" y="50" width="50" height="50" fill="#00ff00"/></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc)
    layers = extract_layers(shapes, mode="color")
    assert len(layers) == 2, f"expected 2, got {len(layers)}"
    print("test_color_mode PASSED")

def test_transform_matrix():
    # translate(10, 20)
    mat = parse_transform("translate(10, 20)")
    pts = np.array([[0, 0]], dtype=float)
    result = apply_matrix(mat, pts)
    assert abs(result[0, 0] - 10) < 0.001
    assert abs(result[0, 1] - 20) < 0.001
    print("test_transform_matrix PASSED")

def test_viewbox_matrix():
    vb = (0, 0, 100, 100)
    mat = build_viewbox_matrix(vb, 200, 200)
    pts = np.array([[0, 0], [100, 100]], dtype=float)
    result = apply_matrix(mat, pts)
    assert abs(result[0, 0] - 0) < 0.001
    assert abs(result[0, 1] - 0) < 0.001
    assert abs(result[1, 0] - 200) < 0.001
    assert abs(result[1, 1] - 200) < 0.001
    print("test_viewbox_matrix PASSED")

def test_aspect_ratio():
    # viewBox 0 0 100 50, output 100 100 -> should letterbox
    vb = (0, 0, 100, 50)
    mat = build_viewbox_matrix(vb, 100, 100)
    pts = np.array([[0, 0], [100, 50]], dtype=float)
    result = apply_matrix(mat, pts)
    # With xMidYMid meet, content is scaled uniformly to fit
    # Scale = min(100/100, 100/50) = min(1, 2) = 1
    # Content occupies 100x50, centered in 100x100 -> y offset = 25
    assert abs(result[1, 1] - 75) < 1, f"expected ~75, got {result[1, 1]}"
    print("test_aspect_ratio PASSED")

def test_compound_path():
    # Path with multiple subpaths (compound path)
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M10 10 L90 10 L90 90 L10 90 Z M30 30 L70 30 L70 70 L30 70 Z" fill="#ff0000"/></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc)
    assert len(shapes) == 1, f"expected 1 shape, got {len(shapes)}"
    # The path should have 2 polygons (outer + hole)
    assert len(shapes[0].polygons) == 2, f"expected 2 polys, got {len(shapes[0].polygons)}"
    print("test_compound_path PASSED")

def test_nested_groups():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><g transform="translate(10,10)"><g id="inner" transform="scale(2)"><rect x="0" y="0" width="10" height="10" fill="#ff0000"/></g></g></svg>'
    doc = parse_svg(svg)
    shapes = normalize(doc)
    assert len(shapes) == 1
    # The rect at 0,0 10x10 with translate(10,10) then scale(2)
    # scale(2) @ translate(10,10) means: scale first (since SVG transforms apply right-to-left from parent)
    # Actually chain = [translate(10,10), scale(2)] composed = translate(10,10) @ scale(2)
    # Point (0,0) -> scale(2) -> (0,0) -> translate(10,10) -> (10,10)
    # Point (10,10) -> scale(2) -> (20,20) -> translate(10,10) -> (30,30)
    s = shapes[0]
    assert s.bbox[0] >= 0 and s.bbox[2] <= 100, f"bbox out of range: {s.bbox}"
    print("test_nested_groups PASSED")

if __name__ == "__main__":
    test_parse_simple()
    test_normalize()
    test_layers()
    test_flat_mode()
    test_color_mode()
    test_transform_matrix()
    test_viewbox_matrix()
    test_aspect_ratio()
    test_compound_path()
    test_nested_groups()
    print("\n=== ALL GEOMETRY TESTS PASSED ===")
