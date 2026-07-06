"""VectorEngine — pure-vector SVG → 3D mesh pipeline.

Uses the geometry module for coordinate normalization, viewBox handling,
and transform resolution. Produces a trimesh Scene from normalized shapes.
"""

import numpy as np
import trimesh
from typing import Any, Optional
from shapely.geometry import Polygon
from shapely.ops import unary_union

from geometry import parse_svg, normalize, extract_layers, Layer, GeometryShape
from materials import apply_color


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
    """Convert hex color to 0-1 RGB tuple."""
    if color.startswith("#") and len(color) == 7:
        try:
            return (
                int(color[1:3], 16) / 255,
                int(color[3:5], 16) / 255,
                int(color[5:7], 16) / 255,
            )
        except ValueError:
            pass
    return (0.39, 0.40, 0.95)


def _extrude_polygon(
    poly: Polygon,
    depth: float,
    color: str,
    metalness: float,
    roughness: float,
) -> Optional[trimesh.Trimesh]:
    """Extrude a 2D polygon into a 3D mesh with proper hole support."""
    if poly.is_empty or not poly.is_valid:
        return None

    exterior = np.array(poly.exterior.coords, dtype=float)
    if len(exterior) < 3:
        return None

    try:
        mesh = trimesh.creation.extrude_polygon(poly, height=depth)
    except Exception:
        # Fallback: fan triangulation of exterior only
        try:
            vertices = np.array(exterior[:, :2], dtype=float)
            faces = [[0, i, i + 1] for i in range(1, len(vertices) - 2)]
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            mesh = mesh.to_3D()
            mesh.apply_translation([0, 0, -depth / 2])
        except Exception:
            return None

    if mesh is None or len(mesh.vertices) == 0:
        return None

    r, g, b = _hex_to_rgb(color)
    apply_color(mesh, color, metalness, roughness)

    return mesh


def _build_shapely_polygon(polys: list[np.ndarray], fill_rule: str = "nonzero") -> Optional[Polygon]:
    """Build a Shapely Polygon from potentially multiple polygon point arrays.

    Handles compound paths: first polygon is exterior, subsequent ones are holes.
    Respects fill rules (evenodd vs nonzero).
    """
    if not polys:
        return None

    # Remove very small degenerate polygons
    valid_polys = []
    for pts in polys:
        if len(pts) < 4:
            continue
        try:
            p = Polygon(pts)
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty and p.area > 1e-10:
                valid_polys.append(p)
        except Exception:
            continue

    if not valid_polys:
        return None

    if len(valid_polys) == 1:
        return valid_polys[0]

    # Multiple polygons: try to assemble compound path
    # Sort by area descending — largest is exterior
    valid_polys.sort(key=lambda p: p.area, reverse=True)
    exterior = valid_polys[0]
    holes = valid_polys[1:]

    if fill_rule == "evenodd":
        # For evenodd, use symmetric difference (XOR) of all polygons
        try:
            result = valid_polys[0]
            for p in valid_polys[1:]:
                result = result.symmetric_difference(p)
            if not result.is_valid:
                result = result.buffer(0)
            return result if not result.is_empty else None
        except Exception:
            pass

    # For nonzero (default), try to create compound polygon with holes
    # Shapely expects holes to be inside the exterior
    try:
        result = Polygon(exterior.exterior.coords, [h.exterior.coords for h in holes if exterior.contains(h)])
        if not result.is_valid:
            result = result.buffer(0)
        return result if not result.is_empty else exterior
    except Exception:
        return exterior


class VectorEngine:
    """SVG to 3D converter for simple vector SVGs.

    Pipeline: SVG → geometry.normalize() → group by color → extrude → Scene
    """

    def __init__(self):
        self.name = "vector"

    def convert(
        self, svg_content: str, settings: dict[str, Any]
    ) -> trimesh.Scene:
        depth = settings.get("depth", 0.5)
        material = settings.get("material", {})
        default_color = material.get("color", "#6366f1")
        metalness = material.get("metalness", 0.2)
        roughness = material.get("roughness", 0.3)
        target_size = settings.get("target_size", 100.0)

        # Parse and normalize SVG
        doc = parse_svg(svg_content)
        shapes = normalize(doc, target_width=target_size, target_height=target_size)

        if not shapes:
            return trimesh.Scene()

        # Group shapes by fill color, merging compound paths
        color_groups: dict[str, list] = {}
        for shape in shapes:
            color = shape.fill if shape.fill != "none" else (shape.stroke if shape.stroke != "none" else default_color)
            color_groups.setdefault(color, []).append(shape)

        scene = trimesh.Scene()
        mesh_idx = 0

        for color, group_shapes in color_groups.items():
            shapely_polys = []
            for shape in group_shapes:
                compound = _build_shapely_polygon(shape.polygons, shape.fill_rule)
                if compound is not None:
                    shapely_polys.append(compound)

            if not shapely_polys:
                continue

            try:
                merged = unary_union(shapely_polys)
            except Exception:
                merged = shapely_polys[0]

            # Handle MultiPolygon result
            polys_to_extrude = []
            if isinstance(merged, Polygon):
                polys_to_extrude = [merged]
            elif hasattr(merged, "geoms"):
                polys_to_extrude = list(merged.geoms)
            else:
                polys_to_extrude = shapely_polys

            for poly in polys_to_extrude:
                mesh = _extrude_polygon(poly, depth, color, metalness, roughness)
                if mesh is not None and len(mesh.vertices) > 0:
                    # Center geometry at origin
                    centroid = mesh.centroid
                    mesh.apply_translation([-centroid[0], -centroid[1], 0])
                    # Stack layers along Z
                    mesh.apply_translation([0, 0, mesh_idx * (depth + 0.02)])
                    scene.add_geometry(mesh, node_name=f"layer_{mesh_idx}")
                    mesh_idx += 1

        return scene

    def convert_to_layers(
        self, svg_content: str, settings: dict[str, Any]
    ) -> list[Layer]:
        """Convert SVG and return structured layers instead of a Scene.

        Used by the layer engine for per-layer editing.
        """
        doc = parse_svg(svg_content)
        shapes = normalize(doc)
        return extract_layers(shapes, mode="auto")
