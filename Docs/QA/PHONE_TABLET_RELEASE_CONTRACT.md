# Havenline: automatic phones/tablets, no unfinished player tests

## User-facing release rule
Kaleb requires one fully functional Android game that automatically adapts to
phones and tablets. He does not want to install or benchmark incomplete builds.
No candidate APK delivery is permitted while the game's required quality gates
are failed, missing or unverified. Internal QA APKs remain necessary for testing;
they are not player deliveries. No new APK is provided with this source update.

Environment work remains the highest priority. Every required environment view
and visual dimension must reach 10/10 from a genuinely executed independent
critic, with no known unresolved defect. Do not rescore unchanged images merely
to obtain a higher number. Char2–4 final rig work remains last, not waived.

## Meaning of zero primitive materials
No blockout geometry, default-looking/unfinished placeholder materials,
primitive-looking buildings/trees, or unreviewed substitutes may ship as finished
art. Authored PBR materials and procedural shaders are legitimate rendering
techniques: their class names are not evidence of quality. The actual rendered
appearance must meet Kaleb's premium stylized winter-survival references.
Visual tests must include silhouettes, close surface detail, all camera angles,
night/weather lighting, real gameplay scale and moving camera occlusion.

## Automatic adaptation
Preserve landscape gameplay, the close camera, four original identities,
automatic proximity actions and unlimited logical carrying. There is no manual
phone/tablet selector. Adapt HUD/control positions and sizes to current window
geometry, pixel density and safe areas. Menus wrap and scroll, and a resize or
fold invalidates stale pointer coordinates without resetting game/save state.
The UI scale must not reduce the native 3D framebuffer or stretch the world.

The deterministic layout matrix includes 16:9 and ultrawide phones, cutouts,
small phones, 16:10/4:3/3:2 tablets, folded/expanded layouts and window offsets.
These are layout fixtures, not actual Android emulation or device approval.
Physical tests must cover installation, touch, screen insets, menu scrolling,
save/reload, suspend/resume, resize and completed-game workloads. Folded and
unfolded use additionally requires uninterrupted saved-state continuity.

## Native 4K/60 and hardware scope
Both internal framebuffer dimensions must remain >=3840x2160 at scale1.0.
A smaller physical panel can display a downsampled 4K internal render; it is not
a physical4K panel. Do not market panel resolution as internal resolution or
lower-resolution upscaling as native4K. Do not silently downgrade the target.

No honest universal claim covers every existing Android GPU. Declare a tested
supported-hardware matrix across phones/tablets/foldables; automatic layout
support does not certify that hardware can sustain4K60. Unsupported or untested
hardware cannot be given a fabricated pass. This is not permission to substitute
one phone-only target for phone-and-tablet support.

Each required hardware case needs the exact same release source/APK, independent
runner/device identity, >=60s warmup, >=1800 continuous measured seconds at the
complete game's worst-case load, raw platform presentation timestamps, matching
native-resolution telemetry, thermal samples and functional evidence.
The validator requires mean presented rate>=60, P99<=16.667ms, no gap>33.334ms,
no native-size/scale drop and no unknown/severe thermal status. Thermal coverage
must span the measurement with <=5s sampling gaps. These numerical checks do
not replace inspection of trace provenance, test actions and a trusted runner.
A lightweight empty scene, fixed-fps recording or desktop software renderer
cannot certify device performance. Never hide pauses or slow samples to pass.

## Executable gate
Run `python tools/havenline/release_gate.py --evidence <bundle-directory>
--source <exact-game-commit> --status HavenlineGodot/data/release-status.json
--output <gate-report.json>` on one line.

The default missing-evidence state is a failure. Required game checks must be
PASS_VERIFIED, not PASS_LOCAL or merely implemented. The manifest is
`release-evidence.json`; it includes source/APK binding, raw critic execution,
14 distinct PNGs with raw responses and six exact10 scores each, and distinct
physical traces for phone, both tablet test cases, and both fold states.
`release_gate.py` defines the fields and required names. Artifact references are
relative paths plus SHA256. Every record must bind the exact source and APK.

This validator checks evidence files, structure and metrics. It is not an AI
critic, a physical testing service or cryptographic proof that a report producer
is truthful. The test harness must establish trustworthy provenance. GitHub
branch protection is not altered by these files. A passing CI code test is not
production permission; the separate release-readiness job remains failing until
actual complete release evidence exists.

## Current state
The existing environment is below10/10. Complete-game features and authored NPC
assets remain missing. Physical phone/tablet4K60 certification is not available.
The player-facing delivery gate stays BLOCKED. The new UI/layout tests and
validator regressions cannot reopen it. No user testing is requested.

## Technical basis
Official guidance checked for this update:
- https://developer.android.com/games/engines/godot/godot-formfactor
- https://developer.android.com/games/develop/multiplatform/support-large-screen-resizability
- https://docs.godotengine.org/en/stable/tutorials/rendering/multiple_resolutions.html
- https://docs.godotengine.org/en/stable/classes/class_displayserver.html
- https://firebase.google.com/docs/test-lab/android/get-started

Firebase Test Lab documents physical-device matrices and game-loop testing.
No compatible device-lab connection was found among this session's available
plugins. Its existence is not authorization, an activated integration or proof
that any device test has run. Do not move this testing burden back to Kaleb.

## Newer reference-video lock retained

`Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md` remains authoritative. Its complete state/motion comparisons and exact 10/10 reference fidelity remain an additional mandatory release requirement. The legacy fourteen environment views are supplemental diagnostic coverage, not permission to preserve the wrong cabin staging or replace the full reference comparison.
