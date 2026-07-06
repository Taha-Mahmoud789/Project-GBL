"""SVG document parser — extracts raw shapes, viewBox, dimensions, defs."""

import re
import numpy as np
from lxml import etree
from dataclasses import dataclass, field
from typing import Optional

NS_SVG = "http://www.w3.org/2000/svg"
NS_XLINK = "http://www.w3.org/1999/xlink"


def _tag(local: str) -> str:
    return f"{{{NS_SVG}}}{local}"


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _parse_float(val: Optional[str], default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val.strip().rstrip("px").rstrip("pt").rstrip("em"))
    except (ValueError, AttributeError):
        return default


def _parse_viewbox(raw: Optional[str]) -> Optional[tuple[float, float, float, float]]:
    if not raw:
        return None
    parts = raw.strip().split()
    if len(parts) == 4:
        try:
            return tuple(float(x) for x in parts)
        except ValueError:
            return None
    return None


def _parse_preserve_aspect_ratio(raw: Optional[str]) -> dict:
    """Parse preserveAspectRatio into x/y meet/slice info."""
    result = {"x": "xMid", "y": "YMid", "meet_or_slice": "meet"}
    if not raw:
        return result
    parts = raw.strip().split()
    if len(parts) >= 1:
        result["x"] = parts[0]
    if len(parts) >= 2:
        result["y"] = parts[1]
    if len(parts) >= 3:
        result["meet_or_slice"] = parts[2]
    return result


@dataclass
class RawShape:
    """A single SVG shape element with its attributes and parent transforms."""
    tag: str  # path, rect, circle, ellipse, polygon, polyline, line, image
    attributes: dict = field(default_factory=dict)
    # Accumulated transform chain from root to this element (list of 3x3 matrices)
    transform_chain: list = field(default_factory=list)
    # Parent group info
    group_id: str = ""
    group_name: str = ""
    group_index: int = 0
    # Fill/stroke attributes resolved from element
    fill: str = ""
    stroke: str = ""
    stroke_width: float = 0.0
    opacity: float = 1.0
    fill_rule: str = "nonzero"
    # For path elements, the raw d attribute
    d: str = ""
    # For image elements
    image_href: str = ""
    image_width: float = 0.0
    image_height: float = 0.0
    image_x: float = 0.0
    image_y: float = 0.0


@dataclass
class SvgDocument:
    """Parsed SVG document with all metadata."""
    # SVG dimensions
    width: float = 0.0
    height: float = 0.0
    viewBox: Optional[tuple[float, float, float, float]] = None
    preserveAspectRatio: dict = field(default_factory=lambda: {
        "x": "xMid", "y": "YMid", "meet_or_slice": "meet"
    })
    # Raw shapes extracted from the tree
    shapes: list = field(default_factory=list)
    # Defs elements (masks, clipPaths, gradients, filters)
    defs: dict = field(default_factory=dict)
    # Named groups for hierarchy
    groups: dict = field(default_factory=dict)
    # Root element reference
    root_tag: str = "svg"


def _collect_styles(el: etree._Element) -> dict:
    """Extract fill, stroke, opacity, fill-rule from element or its style attribute."""
    styles = {}

    # Direct attributes
    for attr in ("fill", "stroke", "opacity", "fill-rule", "stroke-width", "fill-opacity", "stroke-opacity"):
        val = el.get(attr)
        if val is not None:
            styles[attr] = val

    # Style attribute
    style_str = el.get("style", "")
    if style_str:
        for prop in style_str.split(";"):
            prop = prop.strip()
            if ":" in prop:
                key, val = prop.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in ("fill", "stroke", "opacity", "fill-rule", "stroke-width", "fill-opacity", "stroke-opacity"):
                    styles[key] = val

    return styles


def _resolve_color(raw: Optional[str]) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    if raw.lower() in ("none", "transparent", ""):
        return "none"
    return raw


def _walk_tree(
    el: etree._Element,
    parent_matrices: list,
    group_id: str,
    group_name: str,
    group_index: int,
    shapes: list,
    defs_dict: dict,
    depth: int = 0,
) -> None:
    tag = _strip_ns(el.tag)

    # Collect defs elements
    if tag == "defs":
        for child in el:
            child_tag = _strip_ns(child.tag)
            cid = child.get("id", "")
            if cid:
                defs_dict[child_tag + ":" + cid] = child
        return

    # Skip non-renderable elements
    if tag in ("title", "desc", "metadata", "script", "style", "comment"):
        return

    # Handle groups
    if tag in ("g", "svg"):
        local_mat = _parse_local_transform(el)
        chain = parent_matrices + [local_mat] if local_mat is not None else list(parent_matrices)

        # Determine group identity
        gid = el.get("id", group_id)
        gname = el.get("id", "") or group_name

        for i, child in enumerate(el):
            _walk_tree(child, chain, gid, gname, i, shapes, defs_dict, depth + 1)
        return

    # Handle shape elements
    if tag in ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line", "image"):
        local_mat = _parse_local_transform(el)
        chain = parent_matrices + [local_mat] if local_mat is not None else list(parent_matrices)

        styles = _collect_styles(el)
        fill = _resolve_color(styles.get("fill", ""))
        stroke = _resolve_color(styles.get("stroke", ""))
        stroke_width = 0.0
        if "stroke-width" in styles:
            try:
                stroke_width = float(styles["stroke-width"].strip().rstrip("px").rstrip("pt"))
            except ValueError:
                pass

        opacity = 1.0
        if "opacity" in styles:
            try:
                opacity = max(0.0, min(1.0, float(styles["opacity"])))
            except ValueError:
                pass
        # Also check fill-opacity and stroke-opacity
        fill_opacity = 1.0
        if "fill-opacity" in styles:
            try:
                fill_opacity = max(0.0, min(1.0, float(styles["fill-opacity"])))
            except ValueError:
                pass

        fill_rule = styles.get("fill-rule", "nonzero")

        shape = RawShape(
            tag=tag,
            attributes={k: v for k, v in el.attrib.items()},
            transform_chain=chain,
            group_id=group_id,
            group_name=group_name,
            group_index=group_index,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            opacity=opacity * fill_opacity,
            fill_rule=fill_rule,
        )

        if tag == "path":
            shape.d = el.get("d", "")

        if tag == "image":
            shape.image_href = el.get(f"{{{NS_XLINK}}}href") or el.get("href") or ""
            shape.image_width = _parse_float(el.get("width"))
            shape.image_height = _parse_float(el.get("height"))
            shape.image_x = _parse_float(el.get("x"))
            shape.image_y = _parse_float(el.get("y"))

        shapes.append(shape)


def _parse_local_transform(el: etree._Element) -> Optional[np.ndarray]:
    """Parse transform attribute on a single element (not cumulative)."""
    raw = el.get("transform")
    if not raw:
        return None
    from .transforms import parse_transform
    return parse_transform(raw)


def parse_svg(svg_content: str) -> SvgDocument:
    """Parse SVG content into an SvgDocument."""
    root = etree.fromstring(svg_content.encode("utf-8"))
    doc = SvgDocument(root_tag=_strip_ns(root.tag))

    # Parse root SVG dimensions
    doc.width = _parse_float(root.get("width"))
    doc.height = _parse_float(root.get("height"))
    doc.viewBox = _parse_viewbox(root.get("viewBox"))
    doc.preserveAspectRatio = _parse_preserve_aspect_ratio(root.get("preserveAspectRatio"))

    # Walk tree and extract shapes
    defs_dict = {}
    _walk_tree(root, [], "", "", 0, doc.shapes, defs_dict)
    doc.defs = defs_dict

    # If no explicit width/height and no viewBox, use a default
    if doc.width == 0 and doc.height == 0 and doc.viewBox is None:
        # Try to infer from content bounds
        doc.width = 100.0
        doc.height = 100.0

    return doc
