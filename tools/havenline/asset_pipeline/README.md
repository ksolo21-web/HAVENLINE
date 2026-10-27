# HAVENLINE Asset Studio — permanent Blender/PBR/Godot production pipeline

**Scope: ALL Havenline artwork, tasks, animals, biomes, stations, buildings and future assets.** This is not a T05-only tool. It extends—never weakens—the existing `Docs/Production/REFERENCE_STYLE_LOCK_STANDARD.md`, exact image authority, immutable approved baselines and performance contracts.

## Free toolchain

- **Blender**: source-of-truth editable high-detail sculpt (`.blend`) plus separately authored/retopologized game-ready `GAME_LOD0` mesh and UVs. Python automation only for repeatable baking/export.
- **Material Maker** (optional) and **Krita** (optional): create and paint source `base_color.png`, `roughness.png`, and `metallic.png`. Source assets remain visible/editable; we cannot automatically manufacture artistic quality.
- **Blender baking**: native Cycles is available but the Ubuntu Blender 4.0 headless CI fixture currently yields empty UV output, opaque flat-gray normals and black AO. The global gate rejects these maps. A deterministic CPU BVH fallback derives normals via actual high-to-low geometric rays and AO via hemisphere ray intersections. That fallback is limited to 1024px pending high-resolution performance/quality validation; it does not waive the 4K release evidence.
- **glTF 2.0 / Godot 4 Mobile**: export Y-up GLB; validate UV, geometry, material slots, bounds, payload and native renderer. AO is separately exported and **not claimed embedded** in the GLB until the Godot integration step binds it.
- **OpenCV/Pillow**: provenance-bound side-by-side, non-scoring overlay/difference evidence; automatic pixel differences do not equal a fidelity score.
- **Android GPU Inspector / Perfetto / Godot profiler**: real-device draw-call/frame-time/memory evidence, not synthetic CI FPS claims.
- **An independent visual reviewer**: required strict `>9.0` other dimensions and **10/10** reference fidelity and visual language. User reference images take precedence over generative/tool defaults.

These applications are free/open-source. Licenses of external downloaded textures/models still require verification; CI/storage/hardware are not guaranteed free.

## Immutable asset lifecycle

1. **Reference binding.** Create one `asset.json` manifest per object with exact owner image path + SHA-256 and the relevant frozen task manifest. The `family_board` option does **not** satisfy a specific object's final reference.
2. **Editable master.** Sculpt `DETAIL_MASTER` in Blender, with a separately modeled and UV-unwrapped `GAME_LOD0` collection (one joined mesh). Never overwrite an already-approved master. Source `.blend` must retain both.
3. **Painter-authored PBR maps.** Supply PNG atlases `base_color.png`, `roughness.png`, `metallic.png` from Blender/Material Maker/Krita (or properly licensed sources). If an object needs special maps, update its spec; don't make generic default materials look approved.
4. **Bake and export.** Run `blender_build.py`. It preserves the original `.blend`, emits an editable high+low master and separate normal/AO maps, and exports game-ready GLB. **Staging directory only.** No overwrites of `HavenlineGodot/assets`.
5. **Candidate gate.** Run `asset_gate.py candidate` against the exact reference bytes and PBR maps; it checks optimized geometry, source files, shared materials, texture memory estimate, frozen footprint and asset/kit budgets. Technical PASS is not style approval.
6. **Godot checks.** Use `capture_isolated_asset.gd` for seven-angle isolated import diagnostics, then real native shipping-scene captures at fixed cameras, front/rear/left/right/three-quarter/overhead/in-use and night/snow states. Source SHA/GLB hashes bind all evidence.
7. **Reference review.** Use `compare_reference.py` to see exact owner render vs native screenshots and record known defects, but do not let image differences automatically score art. Fix, re-render, critique and re-test.
8. **Performance and release.** Profile actual Android hardware for sustained 60 FPS, thermal state, render calls, textures/memory, interactions, physics, collision, camera, and save behavior. Run independent C1 reference critic at exact 10 for reference fidelity and visual language, all other mandatory axes strictly >9, zero defects; then obtain exact-source user and integration-owner approval. `asset_gate.py release` checks evidence but does not itself deploy or merge.

## Quick commands

Validate manifest structure **without** claiming artwork approved:

```bash
python3 tools/havenline/asset_pipeline/asset_gate.py lint \
  --manifest tools/havenline/asset_pipeline/examples/T05-cooker-asset.json \
  --policy Docs/Production/GLOBAL_ASSET_AUTHORING_POLICY.json
```

Bake a manually authored Blender master (an actual `DETAIL_MASTER` and `GAME_LOD0` collection, with UVs):

```bash
blender -b --factory-startup --python tools/havenline/asset_pipeline/blender_build.py -- \
  --source /workspace/art/asset_master.blend \
  --maps /workspace/art/painted_materials \
  --asset-id asset_name --out /workspace/staging/asset_name \
  --size 1024 --triangles-max 12000 --backend bvh_cpu
```

Complete the SHA-256 and paths in the per-asset manifest, then:

```bash
python3 tools/havenline/asset_pipeline/asset_gate.py candidate \
  --manifest /workspace/staging/asset.json \
  --policy Docs/Production/GLOBAL_ASSET_AUTHORING_POLICY.json \
  --workspace /workspace/staging --report /workspace/staging/technical.json
```

Build image comparisons (**not reference sign-off**):

```bash
python3 tools/havenline/asset_pipeline/compare_reference.py \
 --reference /workspace/staging/references/owner.png \
 --reference-sha256 <exact_owner_image_sha256> \
 --native /workspace/staging/native/front.png \
 --native-scene actual_shipping --asset-id asset_name \
 --source-sha <40-character-commit-SHA> --out /workspace/staging/evidence
```

A source-lint PASS means the data contract exists. A candidate PASS means technical candidate checks passed. A release gate PASS means evidence is complete **but the program still does not merge or replace files automatically.**

## Verified isolated rendering and AO contract (October 26, 2026)

The `havenline-global-godot-framing.yml` workflow reuses an immutable, hash-bound
synthetic smoke GLB from run `40381157048`, avoiding a fresh 190 MB Blender
installation solely to validate Godot camera or material logic.

- **Geometry bake:** run `40379776370` verified real high-to-low projection,
  9 AO shades and 4,092 actual hemisphere-ray occlusions; Khronos 0 errors
  and 0 warnings, explicit tangents and an embedded normal image equal to the
  saved source pixels.
- **Engine import and seven-angle rendering:** run `40381157048` used Godot
  4.7.2 with software OpenGL (llvmpipe); seven true 1280×720 screenshots were
  nonblank and unique. These are not in-game frames or Android measurements.
- **Bounds-based camera:** run `40383973244` passed seven real frames, reducing
  the synthetic orthographic size from 3.80 to 1.95175 with no clipping in the
  inspected views.
- **Separately baked AO:** run `40384710252` imported `ambient_occlusion.png`
  as a Godot texture, bound it to a duplicated inspection-only PBR material,
  and proved actual pixels changed in **all seven** 1280×720 views. Independent
  pixel inspection found 18,509–64,766 changed pixels per view (2.008%–7.028%).
  The AO map is **not automatically included in the GLB** and this proof does
  not modify shipping assets.
- **Native 4K isolated capture:** run `40386019672` passed Godot 4.7.2
  rendering at `3840x2160` for seven genuinely different PNG frames,
  with the identical source-bound synthetic GLB and the AO atlas applied to a
  separate preview material. Evidence artifact `12679779624` was independently
  parsed and its full 4K frame dimensions, hashes and nonblank RGB coverage
  verified. **These are only technical 4K synthetic renders**, using software
  OpenGL; the real Havenline shipping-scene 4K, actual style references and
  physical Android measurements remain untested.
- **Release safeguards:** `asset_gate.py release` now requires native 4K
  source-hash-bound AO off/on frames with real pixel differences, the correct
  separately saved AO atlas SHA, and positive binding evidence **from the true
  Havenline shipping scene**. Isolated proof intentionally fails this release
  criterion. The global source suite passes 14 tests.

Manual isolated AO preview uses the same `capture_isolated_asset.gd` utility:

```bash
godot --path /workspace/isolated-project --rendering-method gl_compatibility \
 --script res://capture.gd -- \
 --glb=res://assets/asset_LOD0.glb \
 --ao=res://assets/ambient_occlusion.png \
 --out=/workspace/ao-evidence --asset-id=asset --width=3840 --height=2160
```

This demonstration only covers a synthetic 128px texture fixture; it does
**not** verify 4K bake speed, the real reference style, production-scene AO
appearance, physical-device FPS, or the required independent visual critic and
owner/integration signoffs.

## Global rollout

The first object with confirmed exact image mapping is T05 cooker `18567.png`. Its existing R07 Blender benchmark is preserved as a technical proof—not promoted because visual fidelity is not approved. T05’s other 19 assets with missing exact source bindings remain blocked for promotion. Use this pipeline for future Havenline biomes, pets, structures, NPCs, production objects and UI-affecting 3D assets using the same reference/style governance.

### Regression and escape hatches

- Existing production assets and Godot scripts remain untouched by this feature; older Python generator and its approved checkpoint stay recoverable.
- All candidates and their evidence are immutable by hash; new changes invalidate affected tests and visual scores, not unrelated approved work.
- A missing tool or hardware device is a **blocked gate**, never an assumed pass.
- “High-poly” is authored only in Blender editable source, never necessarily shipped to phone. UV maps and baked normals/roughness/AO optimize visual fidelity under frozen budgets.
- External free model/texture sources require recorded author/URL/license and license text when applicable. Owner-provided reference renders are reference evidence, not automatically redistributable assets.
- Existing frozen visual reference lock remains exactly **10.0**, even if independent critic dimensions >9.0.

## Current limits

Blender smoke checks and package integration are CI-based. The Cycles backend remains quarantined until actual nonblank normal, AO and UV maps are proven by raster inspection; `FINISHED` is not proof. The BVH CPU fallback is a distinct real-geometry candidate backend, limited to 1024px; a 4K production-rate bake is not validated. The pixel gate rejects both transparent maps and opaque flat-gray-normal/black-AO false positives. A real 3D artist must still sculpt specific reference-accurate geometry; this framework is not an automatic photo-to-perfect-3D system. Actual physical Android C6 and user visual approval remain separate live requirements.
