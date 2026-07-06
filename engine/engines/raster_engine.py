"""RasterEngine — rasterize-and-trace fallback for complex SVGs.

Handles SVGs with masks, clipPaths, filters, embedded images, gradients,
and any other feature that can't be parsed into vector geometry.

Strategy:
  1. Try cairosvg rasterization → contour trace (if cairo available)
  1.5. Decode embedded base64 raster images → contour trace (no cairo needed)
  2. Fallback: strip filters/images, keep paths → vector engine
  3. Last resort: extract all path data directly, ignore effects
"""

import io
import re
import base64
import numpy as np
import trimesh
import cv2
from typing import Any, Optional
from shapely.geometry import Polygon
from lxml import etree

from collections import defaultdict
from shapely.ops import unary_union

from geometry import parse_svg, normalize, extract_layers
from materials import apply_color


def _has_cairo() -> bool:
    try:
        import cairosvg
        return True
    except (ImportError, OSError):
        return False


def _rasterize_svg(svg_content: str, output_size: int = 1024) -> Optional[np.ndarray]:
    """Render SVG to RGBA numpy array using cairosvg."""
    try:
        import cairosvg
        from PIL import Image
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode("utf-8"),
            output_width=output_size,
            output_height=output_size,
        )
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        return np.array(img)
    except Exception:
        return None


def _trace_contours(
    rgba: np.ndarray,
    min_area: float = 10.0,
    simplify_tolerance: float = 1.0,
) -> list[tuple[np.ndarray, str, float]]:
    """Trace contours from RGBA image.

    Returns list of (polygon_points_Nx2, hex_color, opacity).
    Coordinates are in 0-1 normalized space.
    """
    h, w = rgba.shape[:2]
    results = []
    alpha = rgba[:, :, 3]
    rgb = rgba[:, :, :3]

    visible_mask = alpha > 10
    if not np.any(visible_mask):
        return []

    visible_pixels = rgb[visible_mask]
    if len(visible_pixels) == 0:
        return []

    # Extract dominant colors (no sklearn dependency)
    quantized = (visible_pixels >> 3) << 3
    unique, counts = np.unique(quantized.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(-counts)
    palette = unique[order[:20]].astype(np.uint8)

    for color_rgb in palette:
        diff = np.abs(rgb.astype(int) - color_rgb.astype(int))
        color_mask = np.all(diff < 30, axis=2) & visible_mask

        if not np.any(color_mask):
            continue

        mask_u8 = (color_mask * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
        mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            approx = cv2.approxPolyDP(contour, simplify_tolerance, True)
            if len(approx) < 3:
                continue

            pts = approx.reshape(-1, 2).astype(float)
            pts[:, 0] /= w
            pts[:, 1] /= h

            if not np.allclose(pts[0], pts[-1]):
                pts = np.vstack([pts, pts[0:1]])

            cx = max(0, min(w - 1, int(np.mean(contour[:, 0, 0]))))
            cy = max(0, min(h - 1, int(np.mean(contour[:, 0, 1]))))
            opacity = alpha[cy, cx] / 255.0

            r, g, b = int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2])
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            results.append((pts, hex_color, opacity))

    return results


def _trace_embedded_images(svg_content: str) -> list[tuple[np.ndarray, str, float]]:
    """Decode base64-embedded images from SVG and trace their contours.

    Handles "raster-in-SVG" files where the visual content is a PNG/JPEG
    inside an <image> element rather than vector geometry.
    """
    try:
        root = etree.fromstring(svg_content.encode("utf-8"))
    except Exception:
        return []

    NS_SVG = "http://www.w3.org/2000/svg"
    NS_XLINK = "http://www.w3.org/1999/xlink"
    from PIL import Image

    all_contours = []
    for el in root.iter(f"{{{NS_SVG}}}image"):
        href = el.get(f"{{{NS_XLINK}}}href") or el.get("href") or ""
        if not href.startswith("data:image/"):
            continue
        match = re.match(r"data:image/\w+;base64,(.+)", href, re.DOTALL)
        if not match:
            continue
        try:
            raw = base64.b64decode(match.group(1))
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            rgba = np.array(img)
            contours = _trace_contours(rgba, min_area=5.0, simplify_tolerance=1.5)
            all_contours.extend(contours)
        except Exception:
            continue

    return all_contours


def _strip_complex_effects(svg_content: str) -> str:
    """Remove filters, masks, clipPaths, embedded images from SVG.

    Preserves paths, rects, circles, ellipses, polygons, groups.
    Removes everything that can't be parsed into vector geometry.
    """
    NS = "http://www.w3.org/2000/svg"
    try:
        root = etree.fromstring(svg_content.encode("utf-8"))
    except Exception:
        return svg_content

    # Remove <defs> (contains masks, clipPaths, gradients, filters, patterns)
    for defs in root.iter(f"{{{NS}}}defs"):
        parent = defs.getparent()
        if parent is not None:
            parent.remove(defs)

    # Remove <filter> elements anywhere
    for el in list(root.iter(f"{{{NS}}}filter")):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    # Remove <mask> elements
    for el in list(root.iter(f"{{{NS}}}mask")):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    # Remove <clipPath> elements
    for el in list(root.iter(f"{{{NS}}}clipPath")):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    # Remove <image> elements (embedded raster)
    for el in list(root.iter(f"{{{NS}}}image")):
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)

    # Remove filter attributes from remaining elements
    for el in root.iter():
        for attr in list(el.attrib.keys()):
            if "filter" in attr.lower():
                del el.attrib[attr]
        # Remove clip-path and mask references
        for attr in list(el.attrib.keys()):
            if attr in (f"{{{NS}}}clip-path", "clip-path", f"{{{NS}}}mask", "mask"):
                del el.attrib[attr]

    return etree.tostring(root, encoding="unicode", xml_declaration=False)


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    if color.startswith("#") and len(color) == 7:
        try:
            return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
        except ValueError:
            pass
    return (100, 100, 240)


def _extrude_polygon(
    poly: Polygon, depth: float, color: str, metalness: float, roughness: float,
) -> Optional[trimesh.Trimesh]:
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
    apply_color(mesh, color, metalness, roughness)
    return mesh


class RasterEngine:
    """SVG to 3D converter using rasterize-and-trace approach.

    Handles ANY SVG including those with masks, clipPaths, filters, images.

    Strategy:
      1. If cairo available: render SVG → trace contours
      2. Otherwise: strip complex effects → vector engine fallback
    """

    def __init__(self):
        self.name = "raster"

    def convert(self, svg_content: str, settings: dict[str, Any]) -> trimesh.Scene:
        depth = settings.get("depth", 0.5)
        material = settings.get("material", {})
        default_color = material.get("color", "#6366f1")
        metalness = material.get("metalness", 0.2)
        roughness = material.get("roughness", 0.3)
        target_size = settings.get("target_size", 100.0)
        render_size = settings.get("render_size", 1024)

        # Path 1: cairosvg rasterize + trace
        if _has_cairo():
            rgba = _rasterize_svg(svg_content, output_size=render_size)
            if rgba is not None:
                contours = _trace_contours(rgba, min_area=5.0, simplify_tolerance=1.5)
                if contours:
                    return self._build_scene_from_traces(contours, depth, metalness, roughness, target_size)

        # Path 1.5: decode embedded raster images → trace (no cairo needed)
        contours = _trace_embedded_images(svg_content)
        if contours:
            return self._build_scene_from_traces(contours, depth, metalness, roughness, target_size)

        # Path 2: strip effects → vector fallback with timeout
        simplified = _strip_complex_effects(svg_content)
        scene = self._vector_convert_with_timeout(simplified, settings, timeout=10)
        if scene is not None and len(scene.geometry) > 0:
            return scene

        # Path 3: extract individual shapes, skip paths that hang
        scene = self._extract_safe_shapes(svg_content, settings)
        if scene is not None and len(scene.geometry) > 0:
            return scene

        return trimesh.Scene()

    @staticmethod
    def _vector_convert_with_timeout(svg_content: str, settings: dict, timeout: float = 10) -> Optional[trimesh.Scene]:
        """Run VectorEngine.convert() with a timeout to avoid hangs on bad path data."""
        import threading
        result = [None]
        error = [None]

        def _run():
            try:
                from engines.vector_engine import VectorEngine
                result[0] = VectorEngine().convert(svg_content, settings)
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            return None  # timed out
        if error[0] is not None:
            return None
        return result[0]

    def _build_scene_from_traces(
        self, traces, depth, metalness, roughness, target_size
    ) -> trimesh.Scene:
        scene = trimesh.Scene()
        by_color = defaultdict(list)
        for pts, color, opacity in traces:
            try:
                poly = Polygon(pts)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if not poly.is_empty:
                    by_color[color].append(poly)
            except Exception:
                continue
        for i, (color, polys) in enumerate(by_color.items()):
            try:
                merged = unary_union(polys)
                geoms = [merged] if merged.geom_type == "Polygon" else list(merged.geoms)
                for j, poly in enumerate(geoms):
                    mesh = _extrude_polygon(poly, depth, color, metalness, roughness)
                    if mesh is None or len(mesh.vertices) == 0:
                        continue
                    mesh.apply_scale([target_size, target_size, 1])
                    centroid = mesh.centroid
                    mesh.apply_translation([-centroid[0], -centroid[1], 0])
                    mesh.apply_translation([0, 0, i * (depth + 0.02)])
                    scene.add_geometry(mesh, node_name=f"color_{i}_{j}")
            except Exception:
                continue
        return scene

    def _extract_safe_shapes(
        self, svg_content: str, settings: dict[str, Any]
    ) -> Optional[trimesh.Scene]:
        """Extract simple shapes (rect, circle, ellipse) from SVG, skipping problematic paths.

        This is a last-resort fallback for SVGs where even the stripped vector
        engine hangs (e.g., paths with complex arc commands).
        """
        from lxml import etree
        from geometry.transforms import parse_transform, apply_matrix, build_viewbox_matrix, compose_chain

        NS_SVG = "http://www.w3.org/2000/svg"
        depth = settings.get("depth", 0.5)
        material = settings.get("material", {})
        default_color = material.get("color", "#6366f1")
        metalness = material.get("metalness", 0.2)
        roughness = material.get("roughness", 0.3)
        target_size = settings.get("target_size", 100.0)

        try:
            root = etree.fromstring(svg_content.encode("utf-8"))
        except Exception:
            return None

        # Get viewBox
        vb_raw = root.get("viewBox")
        if vb_raw:
            parts = vb_raw.strip().split()
            vb = tuple(float(x) for x in parts) if len(parts) == 4 else None
        else:
            w = float(root.get("width", 100) or 100)
            h = float(root.get("height", 100) or 100)
            vb = (0, 0, w, h)

        if not vb:
            return None

        par_raw = root.get("preserveAspectRatio")
        par = {"x": "xMid", "y": "YMid", "meet_or_slice": "meet"}
        if par_raw:
            parts = par_raw.strip().split()
            if len(parts) >= 1: par["x"] = parts[0]
            if len(parts) >= 2: par["y"] = parts[1]
            if len(parts) >= 3: par["meet_or_slice"] = parts[2]

        vb_mat = build_viewbox_matrix(vb, target_size, target_size, par)

        scene = trimesh.Scene()
        mesh_idx = 0

        def _walk(el, chain):
            nonlocal mesh_idx
            tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

            if tag in ("defs", "metadata", "title", "desc", "style", "script", "filter", "mask", "clipPath"):
                return

            local_mat = parse_transform(el.get("transform"))
            cur_chain = chain + [local_mat] if local_mat is not None else list(chain)
            full_mat = compose_chain(cur_chain)
            full_mat = vb_mat @ full_mat

            if tag == "rect":
                x = float(el.get("x", 0))
                y = float(el.get("y", 0))
                w = float(el.get("width", 0))
                h = float(el.get("height", 0))
                if w > 0 and h > 0:
                    pts = np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h], [x, y]], dtype=float)
                    transformed = apply_matrix(full_mat, pts)
                    self._add_mesh_from_pts(scene, transformed, el, default_color, depth, metalness, roughness, mesh_idx)
                    mesh_idx += 1

            elif tag == "circle":
                cx = float(el.get("cx", 0))
                cy = float(el.get("cy", 0))
                r = float(el.get("r", 0))
                if r > 0:
                    angles = np.linspace(0, 2*np.pi, 32, endpoint=False)
                    pts = np.column_stack([cx + r*np.cos(angles), cy + r*np.sin(angles)])
                    pts = np.vstack([pts, pts[0:1]])
                    transformed = apply_matrix(full_mat, pts)
                    self._add_mesh_from_pts(scene, transformed, el, default_color, depth, metalness, roughness, mesh_idx)
                    mesh_idx += 1

            elif tag == "ellipse":
                cx = float(el.get("cx", 0))
                cy = float(el.get("cy", 0))
                rx = float(el.get("rx", 0))
                ry = float(el.get("ry", 0))
                if rx > 0 and ry > 0:
                    angles = np.linspace(0, 2*np.pi, 32, endpoint=False)
                    pts = np.column_stack([cx + rx*np.cos(angles), cy + ry*np.sin(angles)])
                    pts = np.vstack([pts, pts[0:1]])
                    transformed = apply_matrix(full_mat, pts)
                    self._add_mesh_from_pts(scene, transformed, el, default_color, depth, metalness, roughness, mesh_idx)
                    mesh_idx += 1

            elif tag == "polygon":
                raw = el.get("points", "")
                nums = [float(x) for x in re.split(r"[,\s]+", raw.strip()) if x]
                if len(nums) >= 6:
                    pts = np.array([[nums[i], nums[i+1]] for i in range(0, len(nums), 2)], dtype=float)
                    pts = np.vstack([pts, pts[0:1]])
                    transformed = apply_matrix(full_mat, pts)
                    self._add_mesh_from_pts(scene, transformed, el, default_color, depth, metalness, roughness, mesh_idx)
                    mesh_idx += 1

            # Skip <path> — these may hang the parser

            for child in el:
                _walk(child, cur_chain)

        _walk(root, [])

        return scene if len(scene.geometry) > 0 else None

    def _add_mesh_from_pts(self, scene, pts, el, default_color, depth, metalness, roughness, idx):
        """Try to extrude a point array and add to scene."""
        try:
            poly = Polygon(pts[:, :2])
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty or poly.area < 1e-10:
                return

            # Get color from element
            fill = el.get("fill") or ""
            if not fill or fill.lower() == "none":
                fill = el.get("stroke") or default_color
            if fill.lower() == "none":
                fill = default_color

            mesh = _extrude_polygon(poly, depth, fill, metalness, roughness)
            if mesh and len(mesh.vertices) > 0:
                centroid = mesh.centroid
                mesh.apply_translation([-centroid[0], -centroid[1], 0])
                mesh.apply_translation([0, 0, idx * (depth + 0.02)])
                scene.add_geometry(mesh, node_name=f"layer_{idx}")
        except Exception:
            pass
