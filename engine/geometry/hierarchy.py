"""SVG hierarchy extraction — group shapes into named layers."""

from dataclasses import dataclass, field
from typing import Optional
from .normalizer import GeometryShape


@dataclass
class Layer:
    """A named group of shapes corresponding to an SVG group or logical layer."""
    id: str = ""
    name: str = ""
    shapes: list = field(default_factory=list)  # list of GeometryShape
    visible: bool = True
    # Computed bounding box for the layer
    bbox: tuple = (0, 0, 0, 0)
    # Layer depth offset (for z-stacking)
    z_offset: float = 0.0


def _compute_bbox(shapes: list) -> tuple:
    if not shapes:
        return (0, 0, 0, 0)
    min_x = min(s.bbox[0] for s in shapes)
    min_y = min(s.bbox[1] for s in shapes)
    max_x = max(s.bbox[2] for s in shapes)
    max_y = max(s.bbox[3] for s in shapes)
    return (min_x, min_y, max_x, max_y)


def extract_layers(shapes: list, mode: str = "auto") -> list[Layer]:
    """Group GeometryShape objects into layers.

    Modes:
        'auto'     — one layer per group_id (default)
        'flat'     — all shapes in a single layer
        'per-shape' — each shape is its own layer
        'color'    — group by fill color
    """
    if not shapes:
        return []

    if mode == "flat":
        layer = Layer(
            id="root",
            name="All Shapes",
            shapes=list(shapes),
        )
        layer.bbox = _compute_bbox(layer.shapes)
        return [layer]

    if mode == "per-shape":
        layers = []
        for i, shape in enumerate(shapes):
            layer = Layer(
                id=shape.id or f"layer_{i}",
                name=shape.group_name or f"Layer {i + 1}",
                shapes=[shape],
            )
            layer.bbox = shape.bbox
            layers.append(layer)
        return layers

    if mode == "color":
        color_groups: dict[str, list] = {}
        for shape in shapes:
            color = shape.fill or shape.stroke or "#000000"
            color_groups.setdefault(color, []).append(shape)
        layers = []
        for i, (color, group_shapes) in enumerate(color_groups.items()):
            layer = Layer(
                id=f"color_{i}",
                name=f"Color {color}",
                shapes=group_shapes,
            )
            layer.bbox = _compute_bbox(group_shapes)
            layers.append(layer)
        return layers

    # Default: 'auto' — group by group_id
    group_map: dict[str, list] = {}
    group_order: list[str] = []

    for shape in shapes:
        gid = shape.group_id or "_ungrouped"
        if gid not in group_map:
            group_map[gid] = []
            group_order.append(gid)
        group_map[gid].append(shape)

    layers = []
    for i, gid in enumerate(group_order):
        group_shapes = group_map[gid]
        name = group_shapes[0].group_name or f"Layer {i + 1}"
        layer = Layer(
            id=gid or f"layer_{i}",
            name=name,
            shapes=group_shapes,
        )
        layer.bbox = _compute_bbox(group_shapes)
        layers.append(layer)

    return layers
