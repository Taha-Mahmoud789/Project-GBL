# Migration Log

## Phase 3 — Geometry Engine ✅ COMPLETED
**Commit:** `ed7647c`
**Files:** engine/geometry/__init__.py, parser.py, transforms.py, normalizer.py, hierarchy.py, engine/engines/vector_engine.py

Implemented:
- SVG coordinate normalization with viewBox/aspect-ratio support
- Transform matrix composition (translate/scale/rotate/matrix/skew)
- Layer extraction from nested `<g>` elements
- Proper path tokenizer with implicit number separation
- Rewritten vector_engine.py to use geometry module
- 11/13 test SVGs pass (2 hang on arc edge cases — deferred)

## Phase 5 — Layer Engine ✅ COMPLETED
**Commit:** `00d4b8a`
**Files:** engine/engines/layer_engine.py

Implemented:
- Per-layer mesh extraction from SVG groups/paths
- Stable layer IDs via MD5 of group_id
- Auto-detect: groups → by SVG structure; no groups → per-shape
- Per-layer color, material, visibility
- Z-stacking with configurable depth/spacing
- convert_to_layers() returns metadata for frontend
- 10/11 test SVGs produce proper layers

## Phase 6 — Complex SVG Engine ✅ COMPLETED
**Commit:** `472c5a3`
**Files:** engine/engines/raster_engine.py

Implemented:
- RasterEngine: handles masks, clipPaths, filters, embedded images
- Strip-complex-effects fallback: removes filters/masks/images → vector fallback
- Safe-shapes fallback: extracts rect/circle/ellipse when vector hangs
- Threaded timeout prevents hangs on problematic arc paths
- 8/11 test SVGs produce valid 3D models
- 3 EMPTY: 2 raster-only (need cairo), 1 arc bug (deferred)

## Test Suite ✅ COMPLETED
**Commit:** `cf9333f`
**Files:** engine/test_comprehensive.py

Results:
- Analyzer: 11/11 SVGs analyzed correctly
- VectorEngine: 10/11 produce meshes (1 known hang)
- LayerEngine: 10/11 produce layers (1 known hang)
- RasterEngine: 8/11 produce meshes (2 need cairo, 1 known hang)
- GLB Export: 8/8 successful exports
- ALL TESTS PASSED

## Known Issues
1. ~~**Arc tokenizer bug:** SVGs with concatenated arc flags (e.g., `0143.399`) hang the path parser.~~ FIXED in commit below.
2. ~~**No cairo on Windows:** GeekCode.svg and bootstrap-original-wordmark.svg are raster-only SVGs that need cairosvg for rasterization.~~ FIXED via embedded image tracing.

## Bug Fix: Arc tokenizer — Phase 3 fix incomplete
**Commit:** `cf9333f` (updated)
**Files:** engine/geometry/normalizer.py

Fixed:
- `_fix_arc_flags`: for-loop used enumerate(args) indices, so a split at j=3 injected rest at j=4 slot but the loop checked original args[4]. Replaced with while-loop using carry-chain for proper flag splitting.
- jquery-plain-wordmark.svg now parses correctly (0.05s, 17 meshes).
- Removed EXPECTED_HANG from test suite — all 11/11 SVGs pass.

## Bug Fix: Arc center calculation missing denominator
**Files:** engine/geometry/normalizer.py

Fixed:
- `_arc_to_polyline`: W3C SVG spec F.6.5 requires `factor = sqrt((rx²·ry² - rx²·y1'² - ry²·x1'²) / (rx²·y1'² + ry²·x1'²))`. Code computed `sqrt(numerator)` without dividing by `sqrt(denominator)`.
- Also fixed `dtheta` calculation: was computing angle to reflection of start through center, not to end point.
- wordpress-plain.svg bbox extents: 6,041,198 → 97.4 (was producing coordinates in millions).
- jquery-plain-wordmark.svg, php-original.svg also corrected.

## Bug Fix: Compound path holes dropped
**Files:** engine/engines/vector_engine.py

Fixed:
- `convert()` flattened all sub-path polygons into one list and ran `unary_union`, which absorbed inner letter polygons into outer rect.
- Now calls `_build_shapely_polygon(polys, fill_rule)` per shape, which properly handles evenodd XOR and nonzero holes.
- javascript-plain.svg: 8 verts (just outer rect) → 662 verts (outer rect + "j" + "S" letters).

## Bug Fix: Embedded image tracing (GeekCode/bootstrap)
**Files:** engine/engines/raster_engine.py

Fixed:
- Added `_trace_embedded_images()`: decodes base64 `<image>` data → OpenCV contour trace.
- Inserted as Path 1.5 in RasterEngine.convert() (no cairo needed).
- GeekCode.svg: 0 → 402 meshes, bootstrap-original-wordmark.svg: 0 → 112 meshes.

## Bug Fix: GLB materials (all exports had zero materials)
**Files:** engine/materials.py (new), engine/engines/vector_engine.py, engine/engines/layer_engine.py, engine/engines/raster_engine.py

Fixed:
- All engines were setting `mesh.visual.vertex_colors` (ColorVisuals) which has no `.material` attribute — GLB exporter skipped materials.
- Created `apply_color()` helper that attaches `TextureVisuals(material=PBRMaterial(...))` with baseColorFactor, metallicFactor, roughnessFactor.
- All 3 engines now use `apply_color()`.
- GLB test now validates materials on every mesh.

## Updated Test Results
- Analyzer: 11/11
- VectorEngine: 11/11 (was 10)
- LayerEngine: 11/11 (was 10)
- RasterEngine: 11/11 (was 8)
- GLB Export: 9/9 with materials (was 8, 0 materials)
- All GLB bboxes in 60-100 range (wordpress was 6M, now 97.4)
- javascript-plain.svg: 662 verts (was 8)
