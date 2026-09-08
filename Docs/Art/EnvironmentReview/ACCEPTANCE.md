# Havenline — reference-faithful environment and release acceptance

Read `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md` and `reference-video-sources.json` first. Kaleb's two supplied videos are the authoritative observable appearance and gameplay benchmark. Environment correction remains the highest priority. Preserve all original models, working saves and prior evidence. C2–C4 rigging fixes and final reviews stay last, not waived. No Unity runtime or build step is allowed.

## Reference evidence is mandatory

Obtain and inspect the actual source recordings or checksum-tracked extracted frames, not just this text or image filenames. The two source hashes and 44 selected timestamps are pinned. Use `tools/havenline/extract_reference_frames.py` to reconstruct evidence from the original uploads. Source recordings and derived images must be accessible to the critic. If not, reference fidelity is UNREVIEWED and blocks approval.

Compare candidate screenshots AND motion with the corresponding reference action/state. Record video ID, requested timestamp, source-video/frame hashes, candidate source/APK hashes and capture names. Exclude phone/YouTube chrome and promotional end-card artwork. Never treat screen-recording frame-rate tags as game-performance proof.

## Composition and finish

Match the bright clean stylized appearance, dense blue-white forest framing, warm cleared work floors, fences, turquoise water, colorful production stations, tall carried/stored goods, green cash, demand bubbles, helpers, crowds and upgrade pads. The current sparse cabin-and-furnace clearing is not the target. More bark noise, realistic detail or polygon count does not establish fidelity.

The earlier requirement that a normal view must show both existing shelters is SUPERSEDED as a composition criterion. Preserve the shelters as assets, but do not force the wrong layout into a reference scene. Preserve the user's custom cast, approved animal roster, landscape adaptation and original identity.

No primitive/blockout stand-ins, default/debug materials, broken silhouettes, unexplained clipping, material seams or unfinished contacts. Intentionally clean sculpted surfaces and repeated trees in the reference are not automatically defects; verify fidelity rather than penalizing the intended art language.

## Required comparison states

1. A: fishing and visible fish pickup.
2. A: processing input, output and carrying.
3. A: customer queues, service, payments and tall money stacks.
4. A: paid intake/conveyor transformation and automated supply.
5. A: wheat/processing/bread-output chain.
6. A: simultaneous production, helpers and vehicle-service presentation.
7. B: harvesting, field encounters and carried stacks.
8. B: fenced camp construction and station layout.
9. B: supply/counter/payment loop.
10. B: weapon upgrade and field combat.
11. B: stockpiles, access gate and repeated field-to-camp play.
12. B: working defensive towers with the economy continuing.

A state absent from the candidate is INCOMPLETE, not waived because the current task is called environment-only. Integrate the visible gameplay needed to assess the environment in use. Do not add unrelated features in place of this priority.

Also require actual Mobile-renderer normal gameplay, front/rear/left/right/three-quarter, native >=3840x2160 at scale 1.0, relevant asset/material closeups, full motion cycles, transfer/camera transitions and additional night/weather scenarios. Inspect full images and relevant crops. No staging-shot-only approval.

## Scoring

Each mandatory dimension must score EXACTLY 10/10: visual/style fidelity; authored materials/finish; camera/composition; gameplay/interaction fidelity; motion/transfer continuity; interface/adaptation; geometric integrity and verified evidence. The lowest dimension determines the result. Every required state/check must be reviewed and pass. This supersedes previous >9 thresholds.

No averaging, rounding, repeated unchanged rescoring, missing-area exclusion or hidden defects. Preserve all independent raw findings, including failed/invalid records. Unsupported observations must be verified against pixels/motion; they are not automatically facts and do not provide an excuse to discard valid failures. Builder self-review, code review, geometry counts and exported APK checks are not an independently executed visual critic.

## Automatic phone AND tablet acceptance

Verify landscape aspect ratios, safe areas, readable text, touch controls, camera/world scale, automatic layout, save/resume and lifecycle on named representative phone and tablet hardware. Include relevant fold transitions. No device-selection menu or user adjustment should be needed for usable layout. Preserve reference composition and actor/item readability; do not stretch the portrait footage or simply letterbox it as the game.

## Separate physical native-4K/60 acceptance

Require internal width >=3840 and height >=2160, render scale 1.0, or larger aspect-correct dimensions as needed, at sustained >=60 FPS on named physical PHONE AND TABLET targets through at least a 30-minute representative full-load run in each category. Retain presented-frame timing, resolution history, thermal/throttling and lifecycle evidence. Include actual production, customers, helpers, combat and weather loads, not an empty scene.

Do not substitute a 4K screenshot, fixed-timestep capture, Linux software benchmark, emulator, engine FPS readout or upscaling. Internal 4K rendering does not assert that a lower-resolution panel displays 4K physical pixels. Do not silently lower the rendering target or claim all Android hardware certified from one sample.

## User handoff gate

Kaleb does not want to test the game until it passes. Do not deliver unfinished APKs or ask him to benchmark them. Internal development export remains allowed. Playable handoff is blocked until full functionality, actual-reference fidelity, independent 10/10 review, zero placeholder art and physical phone/tablet native-4K/60 gates all pass. Missing device access must be reported honestly, not transferred to the user as a testing assignment.

This document is an acceptance specification, not evidence that the game or any new review has passed. Historical 0.4.5 checks and failed reviews remain preserved.
