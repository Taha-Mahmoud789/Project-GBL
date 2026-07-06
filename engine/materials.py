"""Shared material helpers for PBR GLB export."""
import trimesh


def apply_color(mesh: trimesh.Trimesh, hex_color: str, metalness: float = 0.2, roughness: float = 0.3):
    """Attach PBR material to mesh so GLB export includes it."""
    if not hex_color or not hex_color.startswith("#") or len(hex_color) < 7:
        hex_color = "#6366f1"
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    mesh.visual = trimesh.visual.TextureVisuals(
        material=trimesh.visual.material.PBRMaterial(
            baseColorFactor=[r, g, b, 1.0],
            metallicFactor=metalness,
            roughnessFactor=roughness,
        )
    )
