"""Web UI E2E test — test all SVGs through the FastAPI backend."""
import requests, os, json, time, trimesh, io

base = "http://localhost:8000"
test_dir = "../test-svgs"

svgs = sorted([f for f in os.listdir(test_dir) if f.endswith(".svg") and "export" not in f])

print("=" * 70)
print("  WEB UI E2E TEST - All %d SVGs via API" % len(svgs))
print("=" * 70)

passed = 0
failed = 0

for fname in svgs:
    path = os.path.join(test_dir, fname)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        svg = f.read()

    # 1. Analyze
    t0 = time.time()
    r = requests.post(base + "/analyze", json={"svg_content": svg, "file_name": fname})
    analyze = r.json()
    analyze_time = time.time() - t0

    # 2. Convert
    t0 = time.time()
    r = requests.post(base + "/convert", json={
        "svg_content": svg,
        "file_name": fname.replace(".svg", ""),
        "settings": {"depth": 0.5, "bevel": 0.05, "smoothness": 5},
        "material": {"color": "#6366f1", "metalness": 0.2, "roughness": 0.3}
    })
    convert_time = time.time() - t0
    glb_bytes = len(r.content)
    is_glb = r.content[:4] == b"glTF"

    # 3. Validate GLB
    if is_glb and glb_bytes > 100:
        loaded = trimesh.load(io.BytesIO(r.content), file_type="glb")
        meshes = sum(1 for g in loaded.geometry.values() if hasattr(g, "vertices"))
        mats = sum(1 for g in loaded.geometry.values() if hasattr(g, "vertices") and hasattr(g.visual, "material"))
        max_ext = max((g.bounding_box.extents.max() for g in loaded.geometry.values() if hasattr(g, "vertices")), default=0)
    else:
        meshes = 0
        mats = 0
        max_ext = 0

    engine = analyze.get("recommended_engine", "?")
    ok = is_glb and meshes > 0 and mats > 0
    status = "OK" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1

    print("  %s %-40s engine=%-12s meshes=%3d mats=%3d glb=%6dB bbox=%6.1f %.2fs" % (
        status, fname, engine, meshes, mats, glb_bytes, max_ext, convert_time
    ))

print("=" * 70)
print("  RESULTS: %d/%d passed" % (passed, len(svgs)))
print("=" * 70)
