"""Coordinate normalization — resolve transforms, center, scale to output space."""

import re
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from shapely.geometry import Polygon, LineString

from .parser import SvgDocument, RawShape
from .transforms import compose_chain, apply_matrix, extract_bounds


@dataclass
class GeometryShape:
    """A fully normalized shape ready for mesh generation."""
    id: str = ""
    tag: str = ""
    polygons: list = field(default_factory=list)  # list of Nx2 numpy arrays (closed)
    fill: str = ""
    stroke: str = ""
    stroke_width: float = 0.0
    opacity: float = 1.0
    fill_rule: str = "nonzero"
    group_id: str = ""
    group_name: str = ""
    layer_index: int = 0
    # Bounding box in normalized space
    bbox: tuple = (0, 0, 0, 0)
    # Image data (for embedded images)
    image_data: Optional[bytes] = None
    image_width: float = 0.0
    image_height: float = 0.0


def _has_numeric_tokens(tokens: list, start: int, count: int) -> bool:
    """Check that tokens[start:start+count] are all numeric (not command letters)."""
    if start + count > len(tokens):
        return False
    for j in range(start, start + count):
        if tokens[j].isalpha():
            return False
    return True


def _tokenize_path(d: str) -> list:
    """Tokenize SVG path data respecting implicit number separation rules.

    The SVG spec allows numbers to be separated implicitly:
    - After a digit, a new number can start with '.' (10.5.3 = 10.5, .3)
    - After a digit, a new number starting with a digit needs whitespace/comma
    - '-' and '+' always start a new number
    - Commands are single letters
    """
    tokens = []
    i = 0
    n = len(d)

    while i < n:
        c = d[i]

        # Skip whitespace and commas
        if c in " \t\n\r,":
            i += 1
            continue

        # Command letter
        if c.isalpha():
            tokens.append(c)
            i += 1
            continue

        # Number: starts with digit, '.', '-', '+'
        if c.isdigit() or c == '.' or c == '-' or c == '+':
            num = c
            i += 1
            has_dot = (c == '.')

            while i < n:
                nc = d[i]
                if nc.isdigit():
                    num += nc
                    i += 1
                elif nc == '.':
                    if has_dot:
                        # Second decimal point — this is a separator.
                        # E.g., "10.5.3" → "10.5" then ".3"
                        break
                    num += nc
                    has_dot = True
                    i += 1
                elif nc in ('e', 'E'):
                    num += nc
                    i += 1
                    if i < n and d[i] in ('+', '-'):
                        num += d[i]
                        i += 1
                else:
                    break

            tokens.append(num)
            continue

        # Unknown char — skip
        i += 1

    return tokens


def _fix_arc_flags(tokens: list) -> list:
    """Fix combined arc flag tokens like '01' → ['0', '1'].

    SVG arc commands have two flag parameters (large-arc, sweep) that are
    single digits (0 or 1). Some SVGs write them concatenated with adjacent
    numbers (e.g., '0143.399' should be '0', '1', '43.399').

    Uses a carry-chain: when arg_pos=3 splits '0143.399' → '0' + carry '143.399',
    arg_pos=4 picks up carry and splits → '1' + carry '43.399'.
    # ponytail: old for-loop used enumerate(args) indices, so a split at j=3
    # injected rest at the j=4 slot but the loop checked original args[4].
    """
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("a", "A"):
            result.append(tok)
            i += 1
            args = []
            while i < len(tokens) and not tokens[i].isalpha() and len(args) < 7:
                args.append(tokens[i])
                i += 1
            fixed_args = []
            arg_pos = 0
            arg_idx = 0
            rest = None
            while arg_pos < 7:
                if rest is not None:
                    a = rest
                    rest = None
                elif arg_idx < len(args):
                    a = args[arg_idx]
                    arg_idx += 1
                else:
                    break
                if arg_pos in (3, 4) and len(a) >= 2 and a[0] in ('0', '1'):
                    fixed_args.append(a[0])
                    rest = a[1:]
                else:
                    fixed_args.append(a)
                arg_pos += 1
            result.extend(fixed_args)
        else:
            result.append(tok)
            i += 1
    return result


def _path_to_polygons(d: str) -> list[np.ndarray]:
    """Parse SVG path 'd' into list of closed polygon point arrays."""
    tokens = _tokenize_path(d)
    tokens = _fix_arc_flags(tokens)
    polygons: list[np.ndarray] = []
    current_pts: list[list[float]] = []
    cx = cy = sx = sy = 0.0
    i = 0

    while i < len(tokens):
        cmd = tokens[i]
        if cmd.isalpha():
            i += 1
        else:
            cmd = "L"

        if cmd in ("M", "m"):
            while _has_numeric_tokens(tokens, i, 2):
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "m":
                    x += cx; y += cy
                if current_pts:
                    polygons.append(np.array(current_pts, dtype=float))
                    current_pts = []
                current_pts.append([x, y])
                cx, cy = sx, sy = x, y

        elif cmd in ("Z", "z"):
            if current_pts:
                current_pts.append([sx, sy])
                polygons.append(np.array(current_pts, dtype=float))
                current_pts = []
            cx, cy = sx, sy

        elif cmd in ("L", "l"):
            while _has_numeric_tokens(tokens, i, 2):
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "l":
                    x += cx; y += cy
                current_pts.append([x, y])
                cx, cy = x, y

        elif cmd in ("H", "h"):
            while _has_numeric_tokens(tokens, i, 1):
                x = float(tokens[i])
                i += 1
                if cmd == "h":
                    x += cx
                current_pts.append([x, cy])
                cx = x

        elif cmd in ("V", "v"):
            while _has_numeric_tokens(tokens, i, 1):
                y = float(tokens[i])
                i += 1
                if cmd == "v":
                    y += cy
                current_pts.append([cx, y])
                cy = y

        elif cmd in ("C", "c"):
            while _has_numeric_tokens(tokens, i, 6):
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
                x, y = float(tokens[i + 4]), float(tokens[i + 5])
                i += 6
                if cmd == "c":
                    x1 += cx; y1 += cy; x2 += cx; y2 += cy; x += cx; y += cy
                n_sub = 12
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt**3 * cx + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x
                    py = mt**3 * cy + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y
                    current_pts.append([px, py])
                cx, cy = x, y

        elif cmd in ("S", "s"):
            while _has_numeric_tokens(tokens, i, 4):
                x2, y2 = float(tokens[i]), float(tokens[i + 1])
                x, y = float(tokens[i + 2]), float(tokens[i + 3])
                i += 4
                if cmd == "s":
                    x2 += cx; y2 += cy; x += cx; y += cy
                n_sub = 12
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt**3 * cx + 3 * mt**2 * t * cx + 3 * mt * t**2 * x2 + t**3 * x
                    py = mt**3 * cy + 3 * mt**2 * t * cy + 3 * mt * t**2 * y2 + t**3 * y
                    current_pts.append([px, py])
                cx, cy = x, y

        elif cmd in ("Q", "q"):
            while _has_numeric_tokens(tokens, i, 4):
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x, y = float(tokens[i + 2]), float(tokens[i + 3])
                i += 4
                if cmd == "q":
                    x1 += cx; y1 += cy; x += cx; y += cy
                n_sub = 10
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt**2 * cx + 2 * mt * t * x1 + t**2 * x
                    py = mt**2 * cy + 2 * mt * t * y1 + t**2 * y
                    current_pts.append([px, py])
                cx, cy = x, y

        elif cmd in ("T", "t"):
            while _has_numeric_tokens(tokens, i, 2):
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == "t":
                    x += cx; y += cy
                n_sub = 10
                for j in range(1, n_sub + 1):
                    t = j / n_sub
                    mt = 1 - t
                    px = mt**2 * cx + 2 * mt * t * cx + t**2 * x
                    py = mt**2 * cy + 2 * mt * t * cy + t**2 * y
                    current_pts.append([px, py])
                cx, cy = x, y

        elif cmd in ("A", "a"):
            while _has_numeric_tokens(tokens, i, 7):
                rx, ry = float(tokens[i]), float(tokens[i + 1])
                rotation = float(tokens[i + 2])
                large_arc = float(tokens[i + 3]) != 0
                sweep = float(tokens[i + 4]) != 0
                x, y = float(tokens[i + 5]), float(tokens[i + 6])
                i += 7
                if cmd == "a":
                    x += cx; y += cy
                arc_pts = _arc_to_polyline(cx, cy, rx, ry, rotation, large_arc, sweep, x, y)
                for pt in arc_pts[1:]:
                    current_pts.append(pt.tolist())
                cx, cy = x, y
        else:
            i += 1

    if current_pts:
        polygons.append(np.array(current_pts, dtype=float))

    return [p for p in polygons if len(p) >= 4]


def _arc_to_polyline(
    x1: float, y1: float,
    rx: float, ry: float,
    rotation: float,
    large_arc: bool,
    sweep: bool,
    x2: float, y2: float,
    n: int = 24,
) -> np.ndarray:
    """Approximate SVG arc as polyline."""
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
    sq = math.sqrt(max(0, rx_sq * ry_sq - rx_sq * y1p**2 - ry_sq * x1p**2))
    denom = rx_sq * y1p**2 + ry_sq * x1p**2
    factor = sq / math.sqrt(denom) if denom > 0 else 0
    if large_arc == sweep:
        factor = -factor

    cxp = factor * rx * y1p / ry if ry != 0 else 0
    cyp = -factor * ry * x1p / rx if rx != 0 else 0
    cx = cos_r * cxp - sin_r * cyp + (x1 + x2) / 2
    cy = sin_r * cxp + cos_r * cyp + (y1 + y2) / 2

    theta1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx) if rx and ry else 0
    dtheta = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx) - theta1 if rx and ry else 0

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


def _rect_points(attrs: dict) -> Optional[np.ndarray]:
    x = float(attrs.get("x", 0))
    y = float(attrs.get("y", 0))
    w = float(attrs.get("width", 0))
    h = float(attrs.get("height", 0))
    if w <= 0 or h <= 0:
        return None
    rx = float(attrs.get("rx", 0) or attrs.get("ry", 0))
    ry = float(attrs.get("ry", 0) or attrs.get("rx", 0))
    if rx > 0 or ry > 0:
        return _rounded_rect(x, y, w, h, rx, ry)
    return np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=float)


def _rounded_rect(x: float, y: float, w: float, h: float, rx: float, ry: float) -> np.ndarray:
    rx = min(rx, w / 2)
    ry = min(ry, h / 2)
    n = 16
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


def _circle_points(attrs: dict) -> np.ndarray:
    cx = float(attrs.get("cx", 0))
    cy = float(attrs.get("cy", 0))
    r = float(attrs.get("r", 0))
    if r <= 0:
        return np.zeros((0, 2), dtype=float)
    n = max(24, int(r * 8))
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.column_stack([cx + r * np.cos(angles), cy + r * np.sin(angles)])


def _ellipse_points(attrs: dict) -> np.ndarray:
    cx = float(attrs.get("cx", 0))
    cy = float(attrs.get("cy", 0))
    rx = float(attrs.get("rx", 0))
    ry = float(attrs.get("ry", 0))
    if rx <= 0 or ry <= 0:
        return np.zeros((0, 2), dtype=float)
    n = max(24, int(max(rx, ry) * 8))
    angles = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.column_stack([cx + rx * np.cos(angles), cy + ry * np.sin(angles)])


def _polygon_points(attrs: dict) -> Optional[np.ndarray]:
    raw = attrs.get("points", "")
    nums = [float(x) for x in re.split(r"[,\s]+", raw.strip()) if x]
    if len(nums) < 6:
        return None
    return np.array([[nums[i], nums[i + 1]] for i in range(0, len(nums), 2)], dtype=float)


def _shape_to_polygons(shape: RawShape) -> list[np.ndarray]:
    """Convert a RawShape to a list of closed polygon point arrays."""
    tag = shape.tag

    if tag == "path":
        return _path_to_polygons(shape.d)

    if tag == "rect":
        pts = _rect_points(shape.attributes)
        if pts is not None and len(pts) >= 3:
            return [np.vstack([pts, pts[0:1]])]
        return []

    if tag == "circle":
        pts = _circle_points(shape.attributes)
        if len(pts) >= 3:
            return [np.vstack([pts, pts[0:1]])]
        return []

    if tag == "ellipse":
        pts = _ellipse_points(shape.attributes)
        if len(pts) >= 3:
            return [np.vstack([pts, pts[0:1]])]
        return []

    if tag == "polygon":
        pts = _polygon_points(shape.attributes)
        if pts is not None and len(pts) >= 3:
            return [np.vstack([pts, pts[0:1]])]
        return []

    if tag == "polyline":
        pts = _polygon_points(shape.attributes)
        if pts is not None and len(pts) >= 3:
            # Polylines are open — close them for polygon creation
            return [np.vstack([pts, pts[0:1]])]
        return []

    if tag == "line":
        x1 = float(shape.attributes.get("x1", 0))
        y1 = float(shape.attributes.get("y1", 0))
        x2 = float(shape.attributes.get("x2", 0))
        y2 = float(shape.attributes.get("y2", 0))
        # Lines become very thin rectangles via stroke-to-fill
        return []

    return []


def _stroke_to_fill_polygon(pts_closed: np.ndarray, width: float) -> Optional[Polygon]:
    """Convert a stroke path to a filled polygon via buffer."""
    if len(pts_closed) < 2:
        return None
    line = LineString(pts_closed[:, :2])
    return line.buffer(width / 2, cap_style=1, join_style=1)


def normalize(
    doc: SvgDocument,
    target_width: float = 100.0,
    target_height: float = 100.0,
) -> list[GeometryShape]:
    """Normalize SVG document shapes into GeometryShape objects.

    Steps:
    1. Parse shapes from SVG tree
    2. Apply viewBox transform matrix
    3. Apply per-element transform chains
    4. Scale to target dimensions
    5. Center in output space
    """
    from .transforms import build_viewbox_matrix

    # Determine output dimensions
    out_w = target_width
    out_h = target_height

    # Build viewBox → output matrix
    if doc.viewBox:
        vb = doc.viewBox
        par = doc.preserveAspectRatio
        vb_mat = build_viewbox_matrix(vb, out_w, out_h, par)
    elif doc.width > 0 and doc.height > 0:
        # No viewBox — use width/height as the coordinate space
        vb = (0, 0, doc.width, doc.height)
        vb_mat = build_viewbox_matrix(vb, out_w, out_h)
    else:
        # No dimensions at all — use identity
        vb_mat = np.identity(3, dtype=float)

    shapes = []
    shape_idx = 0

    for raw in doc.shapes:
        # Get raw polygons
        raw_polys = _shape_to_polygons(raw)
        if not raw_polys:
            continue

        # Compose full transform chain: element transforms → viewBox transform
        elem_mat = compose_chain(raw.transform_chain)
        full_mat = vb_mat @ elem_mat

        # Transform all polygons
        normalized_polys = []
        for raw_pts in raw_polys:
            transformed = apply_matrix(full_mat, raw_pts[:, :2])
            # Ensure polygon is closed (last == first)
            if len(transformed) >= 3 and not np.allclose(transformed[0], transformed[-1]):
                transformed = np.vstack([transformed, transformed[0:1]])
            normalized_polys.append(transformed)

        if not normalized_polys:
            continue

        # Compute bounding box
        all_pts = np.vstack(normalized_polys)
        bbox = extract_bounds(all_pts)

        # Determine fill polygon for geometry shape
        # Use first polygon for the GeometryShape (multiple polys from compound paths)
        geom = GeometryShape(
            id=f"shape_{shape_idx}",
            tag=raw.tag,
            polygons=normalized_polys,
            fill=raw.fill,
            stroke=raw.stroke,
            stroke_width=raw.stroke_width,
            opacity=raw.opacity,
            fill_rule=raw.fill_rule,
            group_id=raw.group_id,
            group_name=raw.group_name,
            layer_index=shape_idx,
            bbox=bbox,
        )

        # Handle stroke-to-fill for stroke-only shapes
        if raw.fill == "none" and raw.stroke != "none" and raw.stroke_width > 0:
            stroke_polys = []
            for pts in normalized_polys:
                poly = _stroke_to_fill_polygon(pts, raw.stroke_width * (full_mat[0, 0] + full_mat[1, 1]) / 2)
                if poly is not None and not poly.is_empty:
                    exterior = np.array(poly.exterior.coords, dtype=float)
                    stroke_polys.append(exterior)
            if stroke_polys:
                geom.polygons = stroke_polys
                geom.fill = raw.stroke
                geom.stroke = "none"
                geom.stroke_width = 0

        shapes.append(geom)
        shape_idx += 1

    return shapes
