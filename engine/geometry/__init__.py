"""SVG geometry engine — coordinate normalization, viewBox, transforms, hierarchy.

Parses SVG into a flat list of GeometryShape objects with full transform chain
resolved and coordinates normalized to a target output space.

Usage:
    doc = parse_svg(svg_content)
    shapes = normalize(doc, target_width=100, target_height=100)
"""

from .parser import parse_svg, SvgDocument
from .transforms import parse_transform, apply_matrix, build_viewbox_matrix
from .normalizer import normalize, GeometryShape
from .hierarchy import extract_layers, Layer

__all__ = [
    "parse_svg",
    "SvgDocument",
    "parse_transform",
    "apply_matrix",
    "build_viewbox_matrix",
    "normalize",
    "GeometryShape",
    "extract_layers",
    "Layer",
]
