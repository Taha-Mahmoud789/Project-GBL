import trimesh
import io


def export_glb(scene: trimesh.Scene) -> bytes:
    buf = io.BytesIO()
    scene.export(buf, file_type="glb")
    return buf.getvalue()
