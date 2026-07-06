"""VectorEngine — pure-vector SVG → 3D mesh pipeline.

Pipeline:
  SVG string → lxml parse → walk tree → extract shapes + transforms
  → convert each shape to shapely Polygon → group by fill color
  → extrude with trimesh → Scene
"""

import re
import math
import numpy as np
import trimesh
from lxml import etree
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union, transform as shapely_transform
from shapely import affinity
from typing import Any, Optional

NS_SVG = "http://www.w3.org/2000/svg"
NS_MAP = {"svg": NS_SVG}


def _tag(local: str) -> str:
    return f"{{{NS_SVG}}}{local}"


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _parse_color(raw: Optional[str]) -> str:
    if not raw or raw.strip().lower() in ("none", "transparent", ""):
        return "none"
    return raw.strip()


def _parse_opacity(el: etree._Element) -> float:
    raw = el.get("opacity") or el.get("svg:opacity")
    if raw:
        try:
            return max(0.0, min(1.0, float(raw)))
        except ValueError:
            pass
    return 1.0


def _parse_fill_rule(el: etree._Element) -> str:
    for attr in ("fill-rule", "svg:fill-rule"):
        raw = el.get(attr)
        if raw:
            return raw.strip().lower()
    return "nonzero"


def _parse_transform(raw: Optional[str]) -> Optional[np.ndarray]:
    """Parse SVG transform attribute into a 3x3 matrix."""
    if not raw:
        return None
    raw = raw.strip()
    mat = np.identity(3, dtype=float)
    while raw:
        m = re.match(
            r"(translate|scale|rotate|matrix|skewX|skewY)\s*\(([^)]*)\)\s*,?\s*",
            raw,
            re.IGNORECASE,
        )
        if not m:
            break
        op = m.group(1).lower()
        args = [float(x.strip()) for x in m.group(2).split(",") if x.strip()]
        raw = raw[m.end():]
        if op == "translate" and len(args) >= 2:
            t = np.identity(3, dtype=float)
            t[0, 2] = args[0]
            t[1, 2] = args[1]
            mat = t @ mat
        elif op == "scale":
            sx = args[0] if args else 1.0
            sy = args[1] if len(args) > 1 else sx
            s = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], dtype=float)
            mat = s @ mat
        elif op == "rotate" and len(args) >= 1:
            deg = args[0]
            rad = math.radians(deg)
            cx = args[1] if len(args) > 2 else 0
            cy = args[2] if len(args) > 2 else 0
            r = np.array(
                [
                    [math.cos(rad), -math.sin(rad), 0],
                    [math.sin(rad), math.cos(rad), 0],
                    [0, 0, 1],
                ],
                dtype=float,
            )
            if cx != 0 or cy != 0:
                t1 = np.identity(3, dtype=float)
                t1[0, 2] = -cx
                t1[1, 2] = -cy
                t2 = np.identity(3, dtype=float)
                t2[0, 2] = cx
                t2[1, 2] = cy
                mat = t2 @ r @ t1 @ mat
            else:
                mat = r @ mat
        elif op == "matrix" and len(args) >= 6:
            m2 = np.array(
                [
                    [args[0], args[2], args[4]],
                    [args[1], args[3], args[5]],
                    [0, 0, 1],
                ],
                dtype=float,
            )
            mat = m2 @ mat
        elif op == "skewx" and args:
            rad = math.radians(args[0])
            s = np.array(
                [[1, math.tan(rad), 0], [0, 1, 0], [0, 0, 1]], dtype=float
            )
            mat = s @ mat
        elif op == "skewy" and args:
            rad = math.radians(args[0])
            s = np.array(
                [[1, 0, 0], [math.tan(rad), 1, 0], [0, 0, 1]], dtype=float
            )
            mat = s @ mat
    return mat


def _apply_matrix(mat: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Apply 3x3 matrix to Nx2 array of points, return Nx2."""
    n = pts.shape[0]
    h = np.ones((n, 3), dtype=float)
    h[:, :2] = pts
    out = (mat @ h.T).T
    return out[:, :2]


def _rect_to_points(el: etree._Element) -> Optional[np.ndarray]:
    x = float(el.get("x", 0))
    y = float(el.get("y", 0))
    w = float(el.get("width", 0))
    h = float(el.get("height", 0))
    if w <= 0 or h <= 0:
        return None
    rx = float(el.get("rx", 0))
    ry = float(el.get("ry", 0))
    if rx > 0 or ry > 0:
        return _rounded_rect_points(x, y, w, h, rx, ry)
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=float)


def _rounded_rect_points(x: float, y: float, w: float, h: float, rx: float, ry: float) -> np.ndarray:
    rx = min(rx, w / 2)
    ry = min(ry, h / 2)
    n = 12
    pts = []
    corners = [
        (x + rx, y, math.pi, 3 * math.pi / 2),
        (x + w - rx, y, 3 * math.pi / 2, 2 * math.pi),
        (x + w - rx, y + h - ry, 0, math.pi / 2),
        (x + rx, y + h - ry, math.pi / 2, math.pi),
    ]
    for cx, cy, start, end in corners:
        for i in range(n):
            angle = start + (end - start) * i / n
            pts.append([cx + rx * math.cos(angle), cy + ry * math.sin(angle)])
    return np.array(pts, dtype=float)


def _circle_points(el: etree._Element) -> np.ndarray:
    cx = float(el.get("cx", 0))
    cy = float(el.get("cy", 0))
    r = float(el.get("r", 0))
    if r <= 0:
        return np.zeros((0, 2), dtype=float)
    n = max(16, int(r * 6))
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.column_stack([cx + r * np.cos(angles), cy + r * np.sin(angles)])


def _ellipse_points(el: etree._Element) -> np.ndarray:
    cx = float(el.get("cx", 0))
    cy = float(el.get("cy", 0))
    rx = float(el.get("rx", 0))
    ry = float(el.get("ry", 0))
    if rx <= 0 or ry <= 0:
        return np.zeros((0, 2), dtype=float)
    n = max(16, int(max(rx, ry) * 6))
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.column_stack([cx + rx * np.cos(angles), cy + ry * np.sin(angles)])


def _polygon_points(el: etree._Element) -> Optional[np.ndarray]:
    raw = el.get("points", "")
    nums = [float(x) for x in re.split(r"[,\s]+", raw.strip()) if x]
    if len(nums) < 6:
        return None
    pts = np.array([[nums[i], nums[i + 1]] for i in range(0, len(nums), 2)], dtype=float)
    return pts


def _arc_to_points(
    x1: float, y1: float,
    rx: float, ry: float,
    rotation: float,
    large_arc: bool,
    sweep: bool,
    x2: float, y2: float,
    n: int = 16,
) -> np.ndarray:
    """Approximate an SVG arc as polyline points."""
    if rx <= 0 or ry <= 0:
        return np.array([[x2, y2]], dtype=float)
    dx = (x1 - x2) / 2
    dy = (y1 - y2) / 2
    cos_r = math.cos(math.radians(rotation))
    sin_r = math.sin(math.radians(rotation))
    x1p = cos_r * dx + sin_r * dy
    y1p = -sin_r * dx + cos_r * dy
    rx_sq = rx * rx
    ry_sq = ry * ry
    x1p_sq = x1p * x1p
    y1p_sq = y1p * y1p
    scale = math.sqrt(max(0, x1p_sq / rx_sq + y1p_sq / ry_sq))
    if scale > 1:
        rx *= scale
        ry *= scale
        rx_sq = rx * rx
        ry_sq = ry * ry
    num = max(0, rx_sq * y1p_sq + ry_sq * x1p_sq)
    den = max(1e-10, rx_sq * ry_sq - num)
    sq = math.sqrt(max(0, num / den))
    if large_arc == sweep:
        sq = -sq
    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx
    cx = cos_r * cxp - sin_r * cyp + (x1 + x2) / 2
    cy = sin_r * cxp + cos_r * cyp + (y1 + y2) / 2
    theta1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    dtheta = math.atan2(-(y1p - cyp) / ry, -(x1p - cxp) / rx) - theta1
    if sweep:
        if dtheta < 0:
            dtheta += 2 * math.pi
    else:
        if dtheta > 0:
            dtheta -= 2 * math.pi
    pts = []
    for i in range(n + 1):
        t = theta1 + dtheta * i / n
        px = rx * math.cos(t)
        py = ry * math.sin(t)
        fx = cos_r * px - sin_r * py + cx
        fy = sin_r * px + cos_r * py + cy
        pts.append([fx, fy])
    return np.array(pts, dtype=float)


def _path_to_polygons(d: str) -> list[np.ndarray]:
    """Parse SVG path 'd' attribute into list of closed polygon point arrays."""
    tokens = re.findall(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", d)
    polygons: list[np.ndarray] = []
    current_pts: list[list[float]] = []
    cx = 0.0
    cy = 0.0
    sx = 0.0
    sy = 0.0
    i = 0

    while i < len(tokens):
        cmd = tokens[i]
        if cmd.isalpha():
            i += 1
        else:
            cmd = "L"

        if cmd in ("M", "m"):
            while i < len(tokens) and not tokens[i].isalpha():
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                if cmd == "m":
                    x += cx
                    y += cy
                if not current_pts or (current_pts and len(current_pts) > 0):
                    if current_pts:
                        polygons.append(np.array(current_pts, dtype=float))
                        current_pts = []
                current_pts.append([x, y])
                cx, cy = x, y
                sx, sy = x, y
        elif cmd in ("Z", "z"):
            if current_pts:
                current_pts.append([sx, sy])
                polygons.append(np.array(current_pts, dtype=float))
                current_pts = []
            cx, cy = sx, sy
        elif cmd in ("L", "l"):
            while i < len(tokens) and not tokens[i].isalpha():
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                if cmd == "l":
                    x += cx
                    y += cy
                current_pts.append([x, y])
                cx, cy = x, y
        elif cmd in ("H", "h"):
            while i < len(tokens) and not tokens[i].isalpha():
                x = float(tokens[i])
                i += 1
                if cmd == "h":
                    x += cx
                current_pts.append([x, cy])
                cx = x
        elif cmd in ("V", "v"):
            while i < len(tokens) and not tokens[i].isalpha():
                y = float(tokens[i])
                i += 1
                if cmd == "v":
                    y += cy
                current_pts.append([cx, y])
                cy = y
        elif cmd in ("C", "c"):
            while i + 5 < len(tokens) and not tokens[i].isalpha():
                x1 = float(tokens[i])
                y1 = float(tokens[i + 1])
                x2 = float(tokens[i + 2])
                y2 = float(tokens[i + 3])
                x = float(tokens[i + 4])
                y = float(tokens[i + 5])
                i += 6
                if cmd == "c":
                    x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
                n_sub = 8
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    t2 = t * t
                    t3 = t2 * t
                    mt = 1 - t
                    mt2 = mt * mt
                    mt3 = mt2 * mt
                    px = mt3 * cx + 3 * mt2 * t * x1 + 3 * mt * t2 * x2 + t3 * x
                    py = mt3 * cy + 3 * mt2 * t * y1 + 3 * mt * t2 * y2 + t3 * y
                    current_pts.append([px, py])
                cx, cy = x, y
        elif cmd in ("S", "s"):
            while i + 3 < len(tokens) and not tokens[i].isalpha():
                x2 = float(tokens[i])
                y2 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])
                i += 4
                if cmd == "s":
                    x2 += cx; y2 += cy; x += cx; y += cy
                n_sub = 8
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    t2 = t * t
                    t3 = t2 * t
                    mt = 1 - t
                    mt2 = mt * mt
                    mt3 = mt2 * mt
                    px = mt3 * cx + 3 * mt2 * t * cx + 3 * mt * t2 * x2 + t3 * x
                    py = mt3 * cy + 3 * mt2 * t * cy + 3 * mt * t2 * y2 + t3 * y
                    current_pts.append([px, py])
                cx, cy = x, y
        elif cmd in ("Q", "q"):
            while i + 3 < len(tokens) and not tokens[i].isalpha():
                x1 = float(tokens[i])
                y1 = float(tokens[i + 1])
                x = float(tokens[i + 2])
                y = float(tokens[i + 3])
                i += 4
                if cmd == "q":
                    x1 += cx; y1 += cy; x += cx; y += cy
                n_sub = 8
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt * mt * cx + 2 * mt * t * x1 + t * t * x
                    py = mt * mt * cy + 2 * mt * t * y1 + t * t * y
                    current_pts.append([px, py])
                cx, cy = x, y
        elif cmd in ("A", "a"):
            while i + 6 < len(tokens) and not tokens[i].isalpha():
                rx = float(tokens[i])
                ry = float(tokens[i + 1])
                rotation = float(tokens[i + 2])
                large_arc = float(tokens[i + 3]) != 0
                sweep = float(tokens[i + 4]) != 0
                x = float(tokens[i + 5])
                y = float(tokens[i + 6])
                i += 7
                if cmd == "a":
                    x += cx; y += cy
                arc_pts = _arc_to_points(cx, cy, rx, ry, rotation, large_arc, sweep, x, y)
                for pt in arc_pts[1:]:
                    current_pts.append(pt.tolist())
                cx, cy = x, y
        elif cmd in ("T", "t"):
            while i + 1 < len(tokens) and not tokens[i].isalpha():
                x = float(tokens[i])
                y = float(tokens[i + 1])
                i += 2
                if cmd == "t":
                    x += cx; y += cy
                n_sub = 8
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt * mt * cx + 2 * mt * t * cx + t * t * x
                    py = mt * mt * cy + 2 * mt * t * cy + t * t * y
                    current_pts.append([px, py])
                cx, cy = x, y
        else:
            i += 1

    if current_pts:
        polygons.append(np.array(current_pts, dtype=float))

    # Filter degenerate polygons (need at least 3 points + closing point)
    return [p for p in polygons if len(p) >= 4]


def _element_to_points(el: etree._Element) -> Optional[np.ndarray]:
    """Convert an SVG element to a point array."""
    tag = _strip_ns(el.tag)
    if tag == "rect":
        return _rect_to_points(el)
    elif tag == "circle":
        return _circle_points(el)
    elif tag == "ellipse":
        return _ellipse_points(el)
    elif tag == "polygon":
        return _polygon_points(el)
    elif tag == "polyline":
        raw = el.get("points", "")
        nums = [float(x) for x in re.split(r"[,\s]+", raw.strip()) if x]
        if len(nums) < 4:
            return None
        pts = np.array([[nums[i], nums[i + 1]] for i in range(0, len(nums), 2)], dtype=float)
        return pts
    elif tag == "line":
        x1 = float(el.get("x1", 0))
        y1 = float(el.get("y1", 0))
        x2 = float(el.get("x2", 0))
        y2 = float(el.get("y2", 0))
        return np.array([[x1, y1], [x2, y2]], dtype=float)
    elif tag == "path":
        d = el.get("d", "")
        polygons = _path_to_polygons(d)
        if polygons:
            return polygons[0]
    return None


def _el_to_polygons(el: etree._Element) -> list[np.ndarray]:
    tag = _strip_ns(el.tag)
    if tag == "path":
        d = el.get("d", "")
        return _path_to_polygons(d)
    pts = _element_to_points(el)
    if pts is not None and len(pts) >= 3:
        pts_closed = np.vstack([pts, pts[0:1]])
        return [pts_closed]
    return []


def _style_attr(el: etree._Element, name: str) -> Optional[str]:
    """Get a CSS property from the style attribute or direct attribute."""
    raw = el.get(name)
    if raw:
        return raw
    style = el.get("style", "")
    m = re.search(rf"{name}\s*:\s*([^;]+)", style)
    if m:
        return m.group(1).strip()
    return None


def _compute_cumulative_transform(el: etree._Element) -> np.ndarray:
    mats = []
    node = el
    while node is not None:
        t = _parse_transform(node.get("transform"))
        if t is not None:
            mats.append(t)
        node = node.getparent()
    mat = np.identity(3, dtype=float)
    for m in reversed(mats):
        mat = m @ mat
    return mat


def _walk_and_collect(
    el: etree._Element,
    parent_matrix: np.ndarray,
    fill_rule: str,
    results: list[dict],
) -> None:
    tag = _strip_ns(el.tag)

    if tag in ("defs", "metadata", "title", "desc"):
        return

    local_matrix = _parse_transform(el.get("transform"))
    if local_matrix is not None:
        matrix = local_matrix @ parent_matrix
    else:
        matrix = parent_matrix.copy()

    if tag in ("g", "svg"):
        for child in el:
            _walk_and_collect(child, matrix, fill_rule, results)
        return

    if tag in ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line"):
        polys = _el_to_polygons(el)
        if not polys:
            return

        fr = _parse_fill_rule(el) or fill_rule
        fill = _parse_color(_style_attr(el, "fill"))
        opacity = _parse_opacity(el)
        stroke = _parse_color(_style_attr(el, "stroke"))
        stroke_width_raw = _style_attr(el, "stroke-width")
        stroke_width = float(stroke_width_raw) if stroke_width_raw else 0

        for raw_pts in polys:
            transformed = _apply_matrix(matrix, raw_pts)
            pts_closed = np.vstack([transformed, transformed[0:1]])

            if fill == "none" and stroke != "none" and stroke_width > 0:
                poly = _stroke_to_fill(pts_closed, stroke_width)
            elif fill != "none":
                try:
                    if fr == "evenodd":
                        poly = Polygon(pts_closed)
                    else:
                        poly = Polygon(pts_closed)
                except Exception:
                    poly = Polygon(pts_closed)
            else:
                continue

            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue

            results.append({
                "polygon": poly,
                "fill": fill if fill != "none" else (stroke if stroke != "none" else "#000000"),
                "opacity": opacity,
                "fill_rule": fr,
            })


def _stroke_to_fill(pts_closed: np.ndarray, width: float) -> Polygon:
    """Convert a stroke path to a filled polygon using buffer."""
    from shapely.geometry import LineString
    line = LineString(pts_closed)
    return line.buffer(width / 2, cap_style=1, join_style=1)


def _merge_polygons_by_color(
    items: list[dict],
) -> dict[str, list[Polygon]]:
    """Group polygons by fill color and merge overlapping ones."""
    groups: dict[str, list[Polygon]] = {}
    for item in items:
        color = item["fill"]
        poly = item["polygon"]
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty:
            continue
        groups.setdefault(color, []).append(poly)
    merged: dict[str, list[Polygon]] = {}
    for color, polys in groups.items():
        try:
            union = unary_union(polys)
        except Exception:
            union = MultiPolygon(polys)
        if isinstance(union, Polygon):
            merged[color] = [union]
        elif isinstance(union, MultiPolygon):
            merged[color] = list(union.geoms)
        else:
            merged[color] = polys
    return merged


def _extrude_polygon(
    poly: Polygon,
    depth: float,
    bevel: float,
    smoothness: int,
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

    holes = []
    for interior in poly.interiors:
        hole = np.array(interior.coords, dtype=float)
        if len(hole) >= 3:
            holes.append(hole)

    try:
        mesh = trimesh.creation.extrude_polygon(
            poly,
            height=depth,
            engine="triangle",
        )
    except Exception:
        try:
            from shapely.geometry import mapping
            vertices = np.array(exterior[:, :2])
            faces = [[0, i, i + 1] for i in range(1, len(vertices) - 2)]
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            mesh = mesh.to_3D()
            mesh.apply_translation([0, 0, -depth / 2])
        except Exception:
            return None

    if bevel > 0:
        try:
            mesh = mesh.convex_hull
        except Exception:
            pass

    r, g, b = 0.39, 0.40, 0.95
    if color.startswith("#") and len(color) == 7:
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
        except ValueError:
            pass

    mesh.visual.vertex_colors = np.array(
        [int(r * 255), int(g * 255), int(b * 255), 255], dtype=np.uint8
    )

    return mesh


class VectorEngine:
    def __init__(self):
        self.name = "vector"

    def convert(
        self, svg_content: str, settings: dict[str, Any]
    ) -> trimesh.Scene:
        depth = settings.get("depth", 0.5)
        bevel = settings.get("bevel", 0.05)
        smoothness = settings.get("smoothness", 5)
        material = settings.get("material", {})
        default_color = material.get("color", "#6366f1")
        metalness = material.get("metalness", 0.2)
        roughness = material.get("roughness", 0.3)

        root = etree.fromstring(svg_content.encode("utf-8"))
        items: list[dict] = []
        _walk_and_collect(root, np.identity(3, dtype=float), "nonzero", items)

        if not items:
            return trimesh.Scene()

        color_groups = _merge_polygons_by_color(items)

        scene = trimesh.Scene()
        layer_idx = 0

        for color, polys in color_groups.items():
            for poly in polys:
                mesh = _extrude_polygon(
                    poly, depth, bevel, smoothness,
                    color, metalness, roughness,
                )
                if mesh is not None and len(mesh.vertices) > 0:
                    mesh.apply_translation([0, 0, layer_idx * (depth + 0.02)])
                    scene.add_geometry(mesh, node_name=f"layer_{layer_idx}")
                    layer_idx += 1

        return scene
