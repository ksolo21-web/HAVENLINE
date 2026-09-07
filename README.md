# HAVENLINE

The active Android migration is **Godot 4.7.2**, in [`HavenlineGodot/`](HavenlineGodot/). This project builds independently of Unity. The older Unity project remains here as historical source, outside the Android export root.

**This branch is an incomplete development migration, not the finished game.** The user's original premium stylized 3D design, non-primitive visual requirement, four-character crew and 4K/60 minimum remain the acceptance criteria. A successful APK export does not satisfy those criteria.

## Implemented and verified

- Actual Godot runtime and ARM64 APK export with no Unity or IL2CPP libraries.
- Exact supplied Character 1 GLB, including its idle/walk/run clips; recovered distinct C2–C4 V7 sources, preserved byte-for-byte.
- Port of the original contract: screen-relative movement, uncapped inventory, gathering, timed delivery, furnace materials/levels, rescue, construction/repair, companion state, helper gathering/delivery, wolf-wave and frontier-unlock simulation.
- 122 deterministic checks across original gameplay, crew/persistence, candidate motion and performance accounting. These are technical checks, not visual or device approval.
- A native scene for movement/gather/carry/deposit integration review. This is deliberately not the shipping scene; full rendered threats, rescue-helper art, animation beats, collision and connected regions are unfinished.
- Landscape presentation and a fixed 8,294,400-or-more-pixel internal render target. The separate command-line render-review mode discloses its smaller resolution. Neither setting certifies physical Android performance.

## Current evidence and failures

Read [`Docs/AI/HavenlineProjectContext.md`](Docs/AI/HavenlineProjectContext.md) first. [`HavenlineGodot/data/release-status.json`](HavenlineGodot/data/release-status.json) contains the complete release blockers. The initial Godot Vulkan Mobile frame exposed C2–C4 rest poses, incomplete environment art and unfinished composition. The 0.4.1 continuation adds derived crew locomotion and actual renderer evidence; it does not approve the full motion set or environment. Review frames are development evidence, not promotional screenshots.

The original scope still requires the complete action-animation set, all four rigs reviewed at 9/10 or higher, approved environment and enemy/helper art, full rendered defense loop, production chains/jobs, ten connected biomes and their transport, weather/day/night, audio, verified Google identity/cloud saves, and physical Android lifecycle/4K60 acceptance. Those requirements have not been removed or replaced with a smaller definition of “complete.”

## Build and test

Use the pinned engine and matching Android export templates from the [official Godot archive](https://godotengine.org/download/archive/4.7.2-stable/). Android export uses Java 17 and the Android SDK; see the [official Android export instructions](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_android.html).

```bash
python3 tools/havenline/asset_audit.py --output artifacts/assets.json
godot --headless --editor --path HavenlineGodot --import --quit
godot --headless --path HavenlineGodot --script res://tools/bake_crew_motion.gd
for suite in test_simulation test_crew_and_persistence test_motion_and_performance; do
  godot --headless --path HavenlineGodot --script res://tests/$suite.gd
done
godot --headless --path HavenlineGodot --quit-after 5
python3 tools/havenline/configure_android.py --sdk /path/to/android-sdk --java /path/to/java17 --godot /path/to/godot
godot --headless --path HavenlineGodot --export-debug 'Android Review'
```

`.github/workflows/havenline-godot-android.yml` performs the same source checks and produces a signed development artifact on GitHub. Development signing is intentionally separate from a production key. Package: `com.kaleb.havenline.review`. It does not overwrite another installed Havenline package.

The production check must currently fail:

```bash
python3 tools/havenline/asset_audit.py --release
```

Do not change a blocker to PASS without the corresponding actual evidence. No production export preset exists while required gates are open.

## Native continuation 0.4.1

See `Docs/AI/NativeContinuation-2026-09-07.md` for implemented crew jobs, persistence, candidate locomotion, lossless scenery batching and reproducible validation. `Docs/AI/NativeVisualCritic.md` preserves the visual/motion/performance acceptance gate. This remains a development build, not the completed game.
