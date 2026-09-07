# Native build verification — September 7, 2026

**Development review only. This is not the completed game, approved non-primitive art or certified physical-device 4K/60.**

## Exact source and artifact

Repository: `ksolo21-web/HAVENLINE`; branch: `codex/havenline-godot-android`; active project: `HavenlineGodot/`.

Verified branch commit: `b42756a8f58d16a3c1b81696737fa0b9a9c4dcf8`.
GitHub Actions run: `34125429904`, job `101752889912`, all steps succeeded.
The pull-request build checked out snapshot `c041342c2e507897473dea39d694e090dcd66170`. Its native source archive matches the locally tested files byte-for-byte.

Export: Godot 4.7.2, Android ARM64, package `com.kaleb.havenline.review`, version `0.4.1-native-review` (401).
APK size: 76,802,780 bytes.
APK SHA-256: `8a7272375d20f3ea281c3c49597687507e0cb63ce4fe9f2a9b7769496fc3d28a`.

The downloaded APK passed ZIP integrity and eight packaging checks, including the Game category, expected package/version, ARM64 Godot runtime, absence of Unity/IL2CPP native libraries, and all three derived crew motion libraries. Android SDK apksigner verified v2 and v3 signatures. This is CI development signing, not permanent production/update signing. Do not uninstall an existing saved game to work around an incompatible earlier review signature.

## Implemented continuation

The continuation adds timed worker gathering, per-unit delivery, building, repairs and guarding; nearest matching-resource routing; Camp-menu job/resource assignment; lead switching that preserves cargo and the four identities; timed storage delivery; interrupted-task persistence and validated backup recovery. Runtime presentation gates prevent saved invisible threats from causing damage and unrendered workers from granting resources. Full visible encounters remain unfinished.

The original GLBs are unchanged. Uploaded `Character-Rig-Fixed-1.glb` matches Character 1 with SHA-256 `95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099`. C2–C4 use derived idle/walk/run candidates; these are not approved complete action sets or a whole-rig pass.

Pooled carried meshes and resource-transfer feedback, static scenery batching and decorative-tree instancing are integrated without lowering the production render target. Safe-area positioning, pause saving, back-to-Camp behavior and bounded frame-interval recording are implemented, but physical Android lifecycle remains untested.

## Measured evidence and limits

All **122 actual Godot checks passed**: 24 original gameplay, 52 crew/persistence and 46 motion/performance-accounting tests. Bone-length invariants and test counts do not certify visual quality.

The build produced an actual Mobile/Vulkan 1280×720 scene on Mesa llvmpipe software rendering. A separate desktop GL-compatibility capture produced a verified 3840×2160 PNG at render scale 1.0. Both use main-script SHA-256 `c6f83797bf23fe82101de6df6dee18ad8d5b19cc28343ece30890c5e282b77fa`. Neither is a physical Android benchmark or sustained 60-FPS proof.

In the same disclosed GL 720p scene, batching changed draw calls from **1,829 to 294** and submitted primitives from **233,992 to 357,144**. Shared bounds submit more off-screen geometry. This demonstrates draw-submission reduction, not an FPS improvement claim.

## Acceptance decision: NOT ACCEPTED

The inspected scene still has rudimentary tiered conifers, sparse terrain and clipped foreground foliage. It does not meet the requested finished non-primitive art standard. Full action animations, complete gait cycles, feet/toe-off, knees, garment/hand contact and all four whole-rig reviews remain unapproved. No 9/10 score is issued.

Complete rendered rescue/wolf encounters, collision/navigation acceptance, production chains, all ten connected biomes and transport, weather/day/night, sound, Google identity/cloud saves, physical Android/fold lifecycle and sustained native 4K/60 remain unfinished or untested. Do not remove these requirements or redefine the review slice as the complete game.

Keep the original bright premium stylized 3D design, close landscape camera, C1/C2 lead selection, four-character crew, automatic proximity actions, uncapped logical carrying and original progression contract. Historical Unity source remains outside the active native build.

Continuation sources: `HavenlineProjectContext.md`, `HistoricalGameplayLock.md`, `NativeContinuation-2026-09-07.md`, `NativeVisualCritic.md` and `HavenlineGodot/data/release-status.json`.
