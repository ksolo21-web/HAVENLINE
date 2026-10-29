# HAVENLINE — Blender-first T05 asset pipeline (candidate)

**Status:** adopted for evaluation, *not yet integrated or approved*. Existing T05 gameplay, Godot GLBs, Python generator, camera, sockets and material palette remain unchanged. The `T05_cooker_BLENDER_CANDIDATE.glb` is intentionally generated into **CI artifacts only**; it never overwrites `HavenlineGodot/assets/stations_v2/cooker_processor.glb`.

## What this solves
The original T05 kit built meshes through Python `legacy_station_kit_v1.MeshBuilder` and textured most surfaces by generated vertex colors. This approach is reproducible but much harder to sculpt, paint, bevel, UV, stage, rig, and author to the exact owner reference at production quality. Blender becomes the master editable asset format; Python stays responsible for tests, repeatability, optimization, manifests and checks.

## First gated benchmark: cooker
- Primary **owner-provided** source `18567.png`, SHA-256 `729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635`; secondary early camp material language `18607.png`, and furnace material language `Furnace_b080906_4K.png`.
- `t05_cooker_benchmark.py` builds *editable* object-specific geometry (steel enclosed arched front, visible saw, timber input bin with raw meat, processed steel output tray, chimney with snow crown, corner feet and pipework). Material palette is layered PBR with compact **UV-backed baked base-color PNGs**, not uniform vertex colors.
- Saves `T05_cooker_EDITABLE.blend` with its studio setup and packed textures *before* collapsing export meshes; subsequent GLB export groups by material so scene batching remains efficient.
- Four separate **Blender studio** images are for art iteration, **not a substitute** for Godot native 3840x2160 gameplay images, night and blizzard states, Android or physical-device FPS.
- `verify_t05_blender.py` checks a real Blender signature, GLB, dimensions in Y-up Godot space, finite bounds, a limited candidate triangle budget, low material/mesh count, required renders and original catalog footprint (2.45 x 2.30 meters). Audit never marks reference fidelity approved.

## Run locally when Blender is installed
```bash
blender -b --factory-startup --python tools/havenline/blender/t05_cooker_benchmark.py -- --out /tmp/t05-blender
python3 tools/havenline/blender/verify_t05_blender.py --out /tmp/t05-blender --baseline-catalog HavenlineGodot/assets/stations_v2/catalog.json
```
Blender does not need to be installed on the user's computer: the separate workflow `.github/workflows/havenline-t05-blender-benchmark.yml` uses the free Ubuntu Blender package on hosted GitHub Actions and stores the results for inspection.

## Promotion gate (MUST pass before any replacement)
1. Compare side-by-side **every** approved object reference, beginning with cooker `18567.png`, in front/rear/left/right/three-quarter and close-up. User render controls form and finish—Blender default geometry does not.
2. Independent detailed visual critic strictly above **9.0 / 10 on every mandatory axis**, with reference-fidelity match; unresolved defects = FAIL.
3. Check actual Godot native 3840x2160 frames, shipping mobile/isometric scale and lighting (including snow/blizzard/night) and no floating, occlusion, clipping, gate/route obstruction.
4. Preserve all 22 IDs and all frozen sockets, arrangement transforms, bounds, clearance, collisions, gameplay code, T03 gates, T04 camera and save contracts.
5. Prove complete catalog headroom: <=180,000 triangles; <=12 shared visible material slots; <=48 draw calls; <=96 MiB texture GPU memory and <=15 MiB packaged storage delta. Reusing the 11 named materials (or a purpose-built replacement within the frozen material budget) is required; **never quietly add materials to production**.
6. Pass native tests, independent critics, Android/C6 physical performance certification, authorization by the repository's integration owner and explicit user visual approval. Do not merge or promote on local preview alone.

## Subsequent rollout
After a reference-accurate cooker is approved, move the remaining T05 resource, utility, counter, ground-pad and defense families into editable `.blend` source files one at a time. Keep an asset-to-reference matrix, high-resolution painted/baked textures (Krita or Material Maker optionally), optimized GLB export, deterministic metadata and native validation. Retain old Python GLBs as rollback versions throughout migration.

**Blender/modeling software cost: $0.** GitHub Actions compute quotas and artifact storage can still have usage limits or costs.

