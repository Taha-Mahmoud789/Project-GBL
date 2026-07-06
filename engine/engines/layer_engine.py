"""LayerEngine — per-layer SVG → 3D mesh pipeline.

Each SVG group (<g>) becomes an independent mesh layer with its own
depth, material, and color. Layers are named and ordered by SVG structure.

Pipeline: SVG → geometry.normalize() → extract_layers() → per-layer extrude → Scene
"""

import hashlib
import numpy as np
import trimesh
from typing import Any, Optional
from shapely.geometry import Polygon
from shapely.ops import unary_union

from geometry import parse_svg, normalize, extract_layers
from geometry.hierarchy import Layer, _compute_bbox


def _make_layer_id(group_id: str, index: int) -> str:
    """Generate a stable, short ID for a layer."""
    if group_id:
        # Use hash for short but unique ID
        h = hashlib.md5(group_id.encode()).hexdigest()[:8]
        return f"layer_{h}"
    return f"layer_{index}"


def _hex_to_rgb(color: str) -> tuple[float, float, float]:
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
    """Extrude a 2D polygon into a 3D mesh."""
    if poly.is_empty or not poly.is_valid:
        return None

    exterior = np.array(poly.exterior.coords, dtype=float)
    if len(exterior) < 3:
        return None

    try:
        mesh = trimesh.creation.extrude_polygon(poly, height=depth)
    except Exception:
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
    mesh.visual.vertex_colors = np.array(
        [int(r * 255), int(g * 255), int(b * 255), 255], dtype=np.uint8
    )
    return mesh


def _layer_to_shapely(layer: Layer) -> list[Polygon]:
    """Convert a Layer's shapes to Shapely polygons, grouped by color."""
    all_polys = []
    for shape in layer.shapes:
        for pts in shape.polygons:
            if len(pts) < 4:
                continue
            try:
                p = Polygon(pts)
                if not p.is_valid:
                    p = p.buffer(0)
                if not p.is_empty and p.area > 1e-10:
                    all_polys.append(p)
            except Exception:
                continue
    return all_polys


class LayerEngine:
    """SVG to 3D converter with per-layer editing support.

    Each SVG group becomes an independent mesh with its own material.
    Layers can be individually re-exported with different depth/material.

    Pipeline: SVG → geometry.normalize() → extract_layers() → per-layer extrude → Scene
    """

    def __init__(self):
        self.name = "layer"

    def convert(
        self, svg_content: str, settings: dict[str, Any]
    ) -> trimesh.Scene:
        depth = settings.get("depth", 0.5)
        bevel = settings.get("bevel", 0.0)
        material = settings.get("material", {})
        default_color = material.get("color", "#6366f1")
        metalness = material.get("metalness", 0.2)
        roughness = material.get("roughness", 0.3)
        target_size = settings.get("target_size", 100.0)
        layer_mode = settings.get("layer_mode", "auto")

        # Parse and normalize SVG
        doc = parse_svg(svg_content)
        shapes = normalize(doc, target_width=target_size, target_height=target_size)

        if not shapes:
            return trimesh.Scene()

        # Auto-detect: if no groups, use per-shape mode
        has_groups = any(s.group_id for s in shapes)
        if layer_mode == "auto":
            layer_mode = "auto" if has_groups else "per-shape"

        # Extract layers from normalized shapes
        layers = extract_layers(shapes, mode=layer_mode)

        if not layers:
            return trimesh.Scene()

        # Build scene with one mesh per layer
        scene = trimesh.Scene()

        for i, layer in enumerate(layers):
            # Skip invisible layers
            if not layer.visible:
                continue

            # Convert layer shapes to Shapely polygons
            polys = _layer_to_shapely(layer)
            if not polys:
                continue

            # Determine dominant color for this layer
            color_counts: dict[str, float] = {}
            for shape in layer.shapes:
                c = shape.fill if shape.fill != "none" else (shape.stroke if shape.stroke != "none" else default_color)
                color_counts[c] = color_counts.get(c, 0) + shape.bbox[2] * shape.bbox[3]
            color = max(color_counts, key=color_counts.get) if color_counts else default_color

            # Merge overlapping polygons of same color
            try:
                merged = unary_union(polys)
            except Exception:
                merged = polys[0]

            polys_to_extrude = []
            if isinstance(merged, Polygon):
                polys_to_extrude = [merged]
            elif hasattr(merged, "geoms"):
                polys_to_extrude = list(merged.geoms)
            else:
                polys_to_extrude = polys

            for j, poly in enumerate(polys_to_extrude):
                mesh = _extrude_polygon(poly, depth, color, metalness, roughness)
                if mesh is None or len(mesh.vertices) == 0:
                    continue

                # Center geometry at origin
                centroid = mesh.centroid
                mesh.apply_translation([-centroid[0], -centroid[1], 0])

                # Stack layers along Z with spacing
                z_offset = i * (depth + 0.02)
                mesh.apply_translation([0, 0, z_offset])

                layer_id = _make_layer_id(layer.id, i)
                node_name = f"{layer.name}_{layer_id}"
                scene.add_geometry(mesh, node_name=node_name)

        return scene

    def convert_to_layers(
        self, svg_content: str, settings: dict[str, Any]
    ) -> list[dict]:
        """Convert SVG and return layer metadata for the frontend."""
        doc = parse_svg(svg_content)
        shapes = normalize(doc)

        has_groups = any(s.group_id for s in shapes)
        layer_mode = "auto" if has_groups else "per-shape"
        layers = extract_layers(shapes, mode=layer_mode)

        result = []
        for i, layer in enumerate(layers):
            color_counts: dict[str, float] = {}
            for shape in layer.shapes:
                c = shape.fill if shape.fill != "none" else (shape.stroke if shape.stroke != "none" else "#6366f1")
                color_counts[c] = color_counts.get(c, 0) + 1
            color = max(color_counts, key=color_counts.get) if color_counts else "#6366f1"

            result.append({
                "id": _make_layer_id(layer.id, i),
                "name": layer.name or f"Layer {i + 1}",
                "color": color,
                "meshCount": sum(len(s.polygons) for s in layer.shapes),
                "bbox": list(layer.bbox),
                "visible": layer.visible,
            })

        return result
