from xml.etree import ElementTree as ET
from typing import Optional

NS = {"svg": "http://www.w3.org/2000/svg"}
SVG_TAG = f"{{{NS['svg']}}}"
NON_RENDERABLE = {"defs", "mask", "clipPath", "pattern", "filter", "marker"}


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _is_inside_non_renderable(el: ET.Element) -> bool:
    parent = el
    while parent is not None:
        name = _strip_ns(parent.tag)
        if name in NON_RENDERABLE:
            return True
        parent = _find_parent(parent)
    return False


def _find_parent(el: ET.Element) -> Optional[ET.Element]:
    parent_map: dict[ET.Element, ET.Element] = {}
    root = el
    while root is not None:
        for child in root:
            parent_map[child] = root
            _walk_and_map(child, parent_map)
        break
    return parent_map.get(el)


def _walk_and_map(el: ET.Element, m: dict) -> None:
    for child in el:
        m[child] = el
        _walk_and_map(child, m)


def _count_drawable(doc: ET.Element, tag_suffix: str) -> int:
    count = 0
    for el in doc.iter(f"{SVG_TAG}{tag_suffix}"):
        if not _is_inside_non_renderable(el):
            count += 1
    return count


def _get_attrib(el: ET.Element, *keys: str) -> Optional[str]:
    for k in keys:
        v = el.get(k)
        if v is not None:
            return v
    return None


def _collect_colors(el: ET.Element, colors: set[str]) -> None:
    for attr in ("fill", "stroke"):
        val = _get_attrib(el, attr, f"svg:{attr}")
        if val and val.lower() not in ("none", "transparent", ""):
            colors.add(val)


def analyze_svg(svg_content: str) -> dict:
    root = ET.fromstring(svg_content)

    paths = _count_drawable(root, "path")
    rects = _count_drawable(root, "rect")
    circles = _count_drawable(root, "circle")
    ellipses = _count_drawable(root, "ellipse")
    polygons = _count_drawable(root, "polygon")
    polylines = _count_drawable(root, "polyline")
    lines = _count_drawable(root, "line")
    texts = _count_drawable(root, "text")
    groups = _count_drawable(root, "g")
    images = _count_drawable(root, "image")
    uses = _count_drawable(root, "use")

    colors: set[str] = set()
    for el in root.iter():
        _collect_colors(el, colors)

    has_gradients = any(
        True for _ in root.iter(f"{SVG_TAG}linearGradient")
    ) or any(True for _ in root.iter(f"{SVG_TAG}radialGradient"))

    has_defs = any(True for _ in root.iter(f"{SVG_TAG}defs"))
    has_styles = any(True for _ in root.iter(f"{SVG_TAG}style"))
    has_masks = any(True for _ in root.iter(f"{SVG_TAG}mask"))
    has_clip_paths = any(True for _ in root.iter(f"{SVG_TAG}clipPath"))
    has_stroke = any(
        v for el in root.iter() if (v := el.get("stroke")) and v.lower() != "none"
    )

    vector_shapes = paths + rects + circles + ellipses + polygons + polylines + lines
    multi_color = len(colors) > 1
    has_raster = images > 0

    if has_raster:
        svg_type = "raster"
        recommended_engine = "RASTER_TRACE"
    elif multi_color or groups > 1:
        svg_type = "layered"
        recommended_engine = "SVG_LAYER"
    else:
        svg_type = "vector"
        recommended_engine = "SVG_VECTOR"

    warnings = []
    if has_masks:
        warnings.append("SVG contains mask effects")
    if has_clip_paths:
        warnings.append("SVG contains clipPath effects")
    if texts > 0:
        warnings.append("SVG contains text elements (may need conversion to paths)")

    return {
        "type": svg_type,
        "layers": groups or 1,
        "shapes": vector_shapes,
        "colors": sorted(colors),
        "warnings": warnings,
        "recommended_engine": recommended_engine,
        "stats": {
            "paths": paths,
            "rects": rects,
            "circles": circles,
            "ellipses": ellipses,
            "polygons": polygons,
            "lines": lines,
            "texts": texts,
            "images": images,
            "groups": groups,
            "uses": uses,
        },
        "features": {
            "has_gradients": has_gradients,
            "has_defs": has_defs,
            "has_styles": has_styles,
            "has_stroke": has_stroke,
            "has_masks": has_masks,
            "has_clip_paths": has_clip_paths,
            "has_multiple_colors": multi_color,
        },
    }
