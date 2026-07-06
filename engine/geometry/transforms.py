"""SVG transform parsing and matrix operations."""

import re
import math
import numpy as np
from typing import Optional


def parse_transform(raw: str) -> Optional[np.ndarray]:
    """Parse SVG transform attribute into a 3x3 affine matrix.

    Handles: translate, scale, rotate, matrix, skewX, skewY.
    Multiple transforms are composed left-to-right.
    """
    if not raw or not raw.strip():
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
            cos_r = math.cos(rad)
            sin_r = math.sin(rad)
            if len(args) >= 3:
                cx, cy = args[1], args[2]
                # rotate(cx,cy) = translate(cx,cy) * rotate(angle) * translate(-cx,-cy)
                t1 = np.identity(3, dtype=float)
                t1[0, 2] = -cx
                t1[1, 2] = -cy
                r = np.array([
                    [cos_r, -sin_r, 0],
                    [sin_r, cos_r, 0],
                    [0, 0, 1],
                ], dtype=float)
                t2 = np.identity(3, dtype=float)
                t2[0, 2] = cx
                t2[1, 2] = cy
                mat = t2 @ r @ t1 @ mat
            else:
                r = np.array([
                    [cos_r, -sin_r, 0],
                    [sin_r, cos_r, 0],
                    [0, 0, 1],
                ], dtype=float)
                mat = r @ mat

        elif op == "matrix" and len(args) >= 6:
            # SVG matrix: a b c d e f  ->  [[a c e] [b d f] [0 0 1]]
            m2 = np.array([
                [args[0], args[2], args[4]],
                [args[1], args[3], args[5]],
                [0, 0, 1],
            ], dtype=float)
            mat = m2 @ mat

        elif op == "skewx" and args:
            rad = math.radians(args[0])
            s = np.array([
                [1, math.tan(rad), 0],
                [0, 1, 0],
                [0, 0, 1],
            ], dtype=float)
            mat = s @ mat

        elif op == "skewy" and args:
            rad = math.radians(args[0])
            s = np.array([
                [1, 0, 0],
                [math.tan(rad), 1, 0],
                [0, 0, 1],
            ], dtype=float)
            mat = s @ mat

    return mat


def apply_matrix(mat: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Apply 3x3 affine matrix to Nx2 point array. Returns Nx2."""
    n = pts.shape[0]
    h = np.ones((n, 3), dtype=float)
    h[:, :2] = pts
    out = (mat @ h.T).T
    return out[:, :2]


def compose_chain(chain: list) -> np.ndarray:
    """Compose a list of matrices into a single cumulative matrix.

    Applied left-to-right: chain[0] @ chain[1] @ ... @ chain[n]
    """
    mat = np.identity(3, dtype=float)
    for m in chain:
        if m is not None:
            mat = m @ mat
    return mat


def build_viewbox_matrix(
    vb: tuple[float, float, float, float],
    width: float,
    height: float,
    par: Optional[dict] = None,
) -> np.ndarray:
    """Build a matrix that maps SVG viewBox coordinates to output pixel coordinates.

    Args:
        vb: (vx, vy, vw, vh) — the viewBox values
        width: output width in pixels
        height: output height in pixels
        par: preserveAspectRatio dict with keys x, y, meet_or_slice

    Returns:
        3x3 matrix that transforms viewBox coords → output coords
    """
    vx, vy, vw, vh = vb
    if vw <= 0 or vh <= 0:
        return np.identity(3, dtype=float)

    if width <= 0 or height <= 0:
        width = vw
        height = vh

    par = par or {"x": "xMid", "y": "YMid", "meet_or_slice": "meet"}

    # Default (no preserveAspectRatio): stretch to fit
    sx = width / vw
    sy = height / vh

    meet_or_slice = par.get("meet_or_slice", "meet")
    if meet_or_slice in ("meet", "none"):
        # Uniform scale — fit inside viewport
        scale = min(sx, sy)
        sx = sy = scale
    elif meet_or_slice == "slice":
        # Uniform scale — cover viewport
        scale = max(sx, sy)
        sx = sy = scale

    # Compute translation for alignment
    # After scaling, the viewBox content occupies vw*sx x vh*sy
    scaled_w = vw * sx
    scaled_h = vh * sy

    # Alignment offsets
    x_align = par.get("x", "xMid")
    y_align = par.get("y", "YMid")

    if "Min" in x_align:
        tx = 0
    elif "Max" in x_align:
        tx = width - scaled_w
    else:  # Mid
        tx = (width - scaled_w) / 2

    if "Min" in y_align:
        ty = 0
    elif "Max" in y_align:
        ty = height - scaled_h
    else:  # Mid
        ty = (height - scaled_h) / 2

    # Matrix: translate(tx, ty) @ scale(sx, sy) @ translate(-vx, -vy)
    mat = np.identity(3, dtype=float)
    mat[0, 0] = sx
    mat[1, 1] = sy
    mat[0, 2] = tx - vx * sx
    mat[1, 2] = ty - vy * sy
    return mat


def extract_bounds(pts: np.ndarray) -> tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) of a 2D point array."""
    if pts.shape[0] == 0:
        return (0, 0, 0, 0)
    return (float(pts[:, 0].min()), float(pts[:, 1].min()),
            float(pts[:, 0].max()), float(pts[:, 1].max()))
