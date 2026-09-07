# HAVENLINE — native continuation, September 7, 2026

## Active source and product requirement

Continue `ksolo21-web/HAVENLINE`, branch `codex/havenline-godot-android`, project `HavenlineGodot/`. Godot is pinned to 4.7.2. Unity is historical source only and is not used to build or run this Android app. Do not restart a generic game or lower the scope to a vertical slice and call it complete.

`HistoricalGameplayLock.md`, `HavenlineProjectContext.md` and the unchanged reference contract remain authoritative: premium bright stylized 3D, close landscape orthographic camera, four distinct core characters, C1/C2 lead choice, movement-only direct control, proximity actions, unlimited logical carrying, and the full connected-world progression. Native UHD-pixel-budget rendering at sustained 60 FPS remains an acceptance requirement, not a proven capability of every Android device.

## Implemented in 0.4.1 development continuation

- Timed helper gathering, single-unit delivery with a delivery latch, construction, repairs, guarding, nearest matching-resource selection, and separate work/combat clocks. A helper's four-unit routing threshold is not an inventory cap.
- Camp-menu crew assignments, including the resource selected for gathering. Lead changes conserve incoming helper cargo and keep all four identities. There are no manual gather/attack/rescue buttons.
- Timed storage drop-off into the existing camp-material ledger; the furnace still requires both 18 wood AND 6 stone for Level 2.
- Saved jobs, cargo type, delivery/build state and interrupted work progress. Semantic validation and backup recovery also handle a checksum-valid but invalid primary save. Abandoned/dead-target progress is pruned instead of accumulating.
- Native-review capabilities gate both newly scheduled AND already-restored invisible encounters. Missing rescue/NPC5 art cannot create an invisible worker granting resources in the rendered review. Encounter progression is preserved, not silently awarded.
- Derived idle/walk/run animation libraries for C2–C4, sampled from the user-supplied C1 source. Only root displacement and bone rotations transfer; target limb translations and scales are preserved. This is an UNAPPROVED motion candidate, not a claim that hands, feet, garments or action animation are finished.
- Pooled carried-item displays for the selected lead and visible workers, plus actual 3D resource-transfer feedback. The mesh pool does not change inventory.
- Static world surfaces batched by original material; repeated decorative pines instanced. Source GLBs, source vertices and character skinning are unchanged. No lower resolution is used as the optimization.
- Bounded O(1) frame-interval recording, slow-frame counts and percentiles, observed internal resolutions, safe-area positioning, Android back-to-Camp behavior and pause saving. Physical lifecycle and thermal behavior are still unverified.

## Reproducible validation

```sh
Godot_v4.7.2-stable_linux.x86_64 --headless --editor --path HavenlineGodot --import --quit
Godot_v4.7.2-stable_linux.x86_64 --headless --path HavenlineGodot --script res://tools/bake_crew_motion.gd
for suite in test_simulation test_crew_and_persistence test_motion_and_performance; do
  Godot_v4.7.2-stable_linux.x86_64 --headless --path HavenlineGodot --script res://tests/$suite.gd
done
```

The suite currently has 122 checks: 24 original gameplay, 52 crew/persistence and 46 motion/performance checks. The generated `assets/motion/*.res` files are build products, not changes to the original rigs. CI bakes them before testing and exporting the isolated ARM64 review APK, verifies its signature and uploads source, logs and a real Mobile-renderer frame.

A 1280×720 software-rendered review is disclosed as such. It cannot prove native 4K/60 performance. `--no-batching` is an A/B diagnostic of the same scene, not a shipping quality tier. Engine interval percentiles are not GPU/display-present timings.

## Release remains blocked

Do not label the review APK as the completed game or certify it from successful compilation, this test count, source hashes, bone-length invariants, or one screenshot.

Remaining production work includes approved non-primitive environment/enemy/NPC art; full action sets and whole-rig review; complete rendered opening encounters; production chains; all ten connected biomes and transports; weather/day/night; Google identity and verified cloud saves; audio; physical fold/lifecycle acceptance; and sustained physical-device 4K/60 validation. These remain in `data/release-status.json`.

Development package: `com.kaleb.havenline.review`, version code 401. It does not overwrite the older `com.kaleb.havenline` app. Its current key is a CI-generated development key, NOT the permanent production/update signing key. A review built with a different key will not update a previous signed review in place; do not recommend uninstalling an existing saved game as a substitute for a proper production signing migration.

## Next work

Inspect the real Mobile frames and full motion cycles, then finish approved action animation and visible rescue/threat art rather than removing the presentation safeguards. Complete the rendered opening sequence before claiming progression into the connected forest. Keep the user's no-Unity, no-primitive and native-performance requirements unchanged.
