# HAVENLINE 0.4.2 build verification

Date: 2026-09-07. DEVELOPMENT ONLY. This document is post-build evidence, not production approval.

## User priority preserved

Characters 2-4 rigging fixes and final rig reviews are deferred to the final character-polish stage. All four custom source GLBs are unchanged. The original C1/C2 lead-selection rules, custom crew, automatic proximity actions, unlimited logical carrying and original furnace/rescue/barricade progression are preserved. Random NPCs do not replace custom characters.

## Delivered code, not delivered NPC art

Implemented separate customer, human survivor/companion and pet state, behavior, save handling and view integration. Customer catalog has two male and two female reusable base-model slots; survivors have distinct male/female slots; initial pets have dog/cat slots. Persistent unique identities, names and appearance descriptors survive reload. Customer queuing and timed resource service protect furnace/construction stocks and prevent duplicate payments. Recruits use conserved timed worker jobs; pets use follow/scout and reject human labor. Legacy saves, semantic validation, partial interactions and backup recovery are covered. Native render sizing now requires both dimensions to meet at least 3840 by 2160, not only equivalent pixel area.

ALL EIGHT NEW AUTHORED MODEL SLOTS ARE STILL MISSING. Zero new NPC visual models were delivered. Appearance descriptors are data only, not applied visible variants. Actual-model-only runtime gates prevent invisible trades, labor and rescues; these gates do not make the visible feature complete. No primitive or custom-character clone fallback is used.

## Build evidence

Built game-source commit: `84a3f1a4f941fd9e024d4e427ab15ab4700578a7`.
Tree: `305d2185047b1385dacae7ee367d4760fff16567`.
Source archive artifact: `10022214740`.
Review/APK artifact: `10022297683`.
Build run/job: `34131399016` / `101772144307`.

200 actual Godot checks passed locally and in the build job: original gameplay 24; crew/save 52; existing motion-data/performance accounting 46; new population 78. Import/headless launch passed. Ten APK inspections passed and apksigner verified v2/v3 signatures. The APK contains ARM64 Godot/C++ libraries and no Unity/IL2CPP native libraries. All 17 changed source files in the archive matched the tested local bytes; all four custom GLB hashes matched their unchanged originals.

The one-time application job passed tests, four Mobile/Vulkan captures, export and signature/inspection, then failed at source push because its Actions token lacked workflow-write permission. The authorized GitHub connector subsequently published the exact existing built commit with a NON-FORCE ref update; a fresh branch read confirmed it. The original run remains failed and is not relabeled successful.

The normal Native Android Review PR workflow then independently executed its build steps (not an independent AI critic): run `34132032262`, job `101774204336`, all steps concluded success for source head `84a3f1a4f941fd9e024d4e427ab15ab4700578a7`. This corroborating run does not change the provenance of the delivered APK listed below.

For future reproduction use `.github/workflows/havenline-godot-android.yml`. Do not reapply the one-time population source-transport patch to the updated branch.

## Visual review and release status

Four actual front/rear/side/three-quarter screenshots were inspected. They use Godot Mobile/Vulkan on software llvmpipe at 1280x720, explicitly in review mode. They are NOT native-4K frames, Android-device tests or sustained-60-fps evidence. Capture timing reports contain zero timing samples and are not benchmarks.

Internal review: BLOCK RELEASE. All new NPC models and full role animations are missing. The camp terrain remains flat/sparse, repeated tiered trees and simplified buildings fall below the requested finished non-primitive quality, and foreground foliage shows clipping/cutaway defects. Complete visible rescue/wolf encounters and the larger original game remain unfinished. No independent AI critic executed, no independent numerical score was assigned, and no >9.0 quality pass is claimed.

The exporter reported No project icon specified and used a default icon. Export/signature succeeded, but the branding defect remains. Permanent development update signing is not configured. Physical Android installation/lifecycle, fold behavior, thermal/frame-pacing tests and sustained native 4K/60 remain unverified. Full production chains, connected biomes/transport, weather/day-night, audio and Google identity/cloud saves remain open.

The packaged release-status.json is the earlier source-preparation snapshot and still marks this APK build untested and population tests local-only. This post-build document supplements it without modifying the immutable delivered APK or removing remaining failed release requirements.

## Delivered APK provenance

File: HAVENLINE-0.4.2-Native-Review-ARM64.apk.
Package: com.kaleb.havenline.review.
Version: 0.4.2-population-review (402).
Bytes: 76832192.
SHA256: ddcb27c8a05a496cc8b8dd9b9d12b538fc94f3d7a9d2b6cf92e4a01343260350.

A previous review installation may reject this development-signing certificate. Do not uninstall an existing saved game merely to bypass a signing conflict. No physical install test is claimed.

## Next executable work

Author/import and review the eight distinct customer/survivor/pet assets and full role animations; apply real appearance variants; complete the rendered customer, rescue and companion loops, then continue the complete original Havenline scope. Keep Characters 2-4 rigging fixes and final full-cycle reviews last. The preserved >9.0 plus every-mandatory-check rule still blocks final release.
