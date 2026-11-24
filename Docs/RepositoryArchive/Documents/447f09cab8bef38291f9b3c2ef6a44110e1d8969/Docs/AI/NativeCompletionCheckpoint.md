# HAVENLINE native completion workstream — 2026-09-07

## Required direction remains unchanged

Build the original Android Havenline entirely without Unity. The active executable project is `HavenlineGodot`, pinned to Godot 4.7.2 Mobile. This is the bright, premium stylized snowbound survival/base-building game, not the separate realistic agent-world project. No primitive/blockout appearance may pass the production gate.

Preserve `reference-contract.json` 1.3.1 and the historical gameplay lock: close landscape camera, C1/C2 selectable leads, the other lead plus C3/C4 as companions, an additional rescued NPC5, unlimited inventory, one movement joystick, automatic proximity actions, furnace L2 at 18 wood AND 6 stone, 2.2-second gated rescue, north barricade at 8 wood AND 3 stone, first 48-second/three-wolf wave, and forest unlock. Full scope still includes production, helpers, ten connected biomes, transport, weather/day-night, audio and verified Google identity/cloud saves. None of these requirements was removed to make a smaller demo pass.

Native 4K/60 or better is the minimum target. Both internal dimensions must meet 3840x2160, preserving the display aspect ratio; a pixel-count-only target is insufficient. Software-rendered CI images and application callbacks do not certify physical Android frame presentation, thermals or sustained frame rate.

## Source and branch

Workstream branch: `codex/havenline-native-completion-20260907`, branched from `3335395f78e1d865502272a3527085c3e9de1f60` on `codex/havenline-godot-android`. Concurrent work on the parent branch is deliberately preserved. Merge only after review; do not force-reset the parent or main.

The uploaded `Character-Rig-Fixed-1.glb` exactly matches `assets/characters/Character1.glb`:
`95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099` (SHA-256).
All four original source GLBs remain unchanged.

## Implemented in this workstream

- `native_simulation.gd`: resolves movement against outpost obstacles before proximity actions; obstacle-aware A* companion paths; follow, wood, stone, metal, fuel and guard assignments; conserved, typed worker cargo; backwards-compatible, atomically validated save extension. Unrendered threats are frozen rather than allowing invisible damage.
- `main_native.gd`: active scene integration, actual minimum-dimension 4K buffers at scale 1, refresh-aware 60/90/120 frame caps, safe-area coordinates, scrollable Camp assignments, visible worker cargo, correct lead-swap control routing, bounded performance-report export, explicit review labelling and capture provenance.
- `native_world_renderer.gd`: GPU instances static forest meshes; harvested trees remain independently visible. Source geometry is not simplified or replaced.
- `tools/build_locomotion.gd`: creates derived idle/walk/run libraries for C2-C4 by mapping 22 body/limb/foot bones from the exact C1 source. These are UNAPPROVED retarget candidates, not a whole-rig or complete action-animation pass. Finger rest poses are preserved; combat/gather/repair/carry action sets still need production work.
- `native_frame_recorder.gd`: fixed-capacity callback samples and internal-dimension observations. Pause/resume and resize break measurement segments. Reports always retain `performance_certified=false` and `physical_device_verified=false`.

## Reproduce

From the repository root, using the pinned engine executable:

```sh
godot --headless --editor --path HavenlineGodot --import --quit
godot --headless --path HavenlineGodot --script res://tools/build_locomotion.gd
godot --headless --editor --path HavenlineGodot --import --quit
for suite in test_simulation test_native_regression test_native_runtime test_native_scene; do
  godot --headless --path HavenlineGodot --script "res://tests/$suite.gd"
done
```

The four suites contain 24 legacy, 24 native regression, 35 native runtime and 12 native scene checks (95 total). Passing them proves those checks only. The workflow additionally produces six pose/view fixtures and a native 3840x2160 Mobile-renderer capture, then an isolated ARM64 development APK and buildable source archive. It fails if rendering falls back to Compatibility, captures are missing, dimensions are wrong or script errors occur.

## Release blockers — do not relabel as complete

The current environment has not passed Kaleb's non-primitive visual standard. C2-C4 derived locomotion needs whole-cycle/multi-angle skinning, foot planting, toe/heel roll, clipping and cadence review. Wolf art and distinct NPC5 art are absent; the rendered opening does not run end-to-end. Full production chains, connected biome travel, weather/day-night, complete sound and Google identity/cloud remain outstanding. Physical Android install/lifecycle/folding and sustained 4K/60 remain untested. `data/release-status.json` stays blocked; no production release is authorized by these development tests.

The review APK uses isolated `com.kaleb.havenline.review`, not the production package. CI-generated development signing is not a permanent production/OAuth signing identity. Do not present this APK as the complete game or an approved production update.
