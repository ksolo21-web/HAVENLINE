# Task 2 completed — terrain, snow, work floor and lakeshore

## Accepted result

**PASS for intermediate Task 2 progression. Minimum score: 9.0/10 in both independent roles. Target remains 10/10.** Every required dimension in all eight evidence groups passed in both roles, with no unresolved mandatory Task 2 defect after actual-image adjudication. Task 3 is ready but has not started. This is not a full-game release or physical-device performance certificate.

Accepted game source: `96f8d396a5015e136c590dc496214a689adb1e43`.
Branch: `codex/havenline-sequential-task-01` (the historical branch name now contains completed T01 and T02 work).
Verified on 2026-09-10. Subsequent changes through `e83bb852a8c99f0d8534d29c174316e4b9a12c82` contain review tooling only; no changed game runtime or assets. The exact source archive, image hashes, test logs and independent raw reviews are preserved.

## What was completed

The sparse ground was replaced by a connected warm peach/brown camp floor, a lakeside work area and dry connecting space, surrounded by snow. The shoreline uses a shared bounded shape for water, bank geometry and dry-land constraints. Rounded snow lips and a physically raised/sloped bank provide real shape instead of relying only on a painted edge. Subtle world-stable surface variation preserves the references' clean stylization; fine detail is derivative-filtered rather than noisy screen-space texture.

Ground and actors use the same triangulated height surface. Lake exclusion and dry-land projection preserve movement, companion routing and old-save recovery without losing inventory. The water is bounded, opaque and driven by the saved simulation clock. No full-screen refraction, transparent water pass, manual interaction substitute or new gameplay scope was added.

The final repair changes `outpost_surface.gd`, `outpost_view.gd`, `outpost_snow.gdshader`, the T02 capture harness and surface-stress assertions. A restrained daylight-only snow fill turns off at night; general scene lighting, normal camera behavior and all approved tree meshes remain unchanged. Low-angle terrain-only profiles are explicitly diagnostic and supplement, never replace, the normal gameplay images.

## Verification

| Evidence | Verified result |
|---|---|
| Executed engine assertions | 726/726 in 13 suites |
| Preserved-tree geometry checks | 9/9 |
| Controlled same-camera light-state checks | 10/10 |
| Final local closure/evidence checks | 124/124 |
| Synthetic grade-validator regression tests | 15/15; checker tests, not game or art approval |
| Actual source-bound Mobile-renderer frames | 51: 45 original plus 6 controlled conditions |
| Native 3840 x 2160 at render scale 1.0 | 14 actual frames |
| Previously protected original/approved GLBs | 33 unchanged |
| Protected main, forest and cutaway runtime files | 3 unchanged |
| Independent role/group reviews | 16 complete, raw-response-bound reviews |

The surface-stress suite also verifies dry-land projection over 6,240 sampled positions and a simulated camp-to-shore route. Old-save relocation preserves inventory. Tree clearance, resource depletion/restoration and original resource quantities remain functional.

The final local closure verifier checked 78 exact runtime/asset hashes, 36 preservation hashes, original PNG bytes, raw executed tests, complete independent report coverage and source-bound reviewer inputs. It did not generate or alter any critic score. All 51 states were inspected using view/sequence sheets and relevant original-resolution close-ups; this is not a claim to have played on Android hardware or reviewed arbitrary unsampled motion.

## Independent scores

| Evidence group | Reference fidelity role | Visual integrity role |
|---|---:|---:|
| Work floor | 9.4 | 9.5 |
| Shoreline | 9.4 | 9.5 |
| Snow/contact | 9.0 | 9.4 |
| Tree visibility | 9.5 | 9.5 |
| Camera route, early | 9.5 | 9.0 |
| Camera route, late | 9.5 | 9.4 |
| Water sequence | 9.0 | 9.5 |
| Expanded night/overview | 9.5 | 9.4 |
| **Lowest required dimension** | **9.0** | **9.0** |

These are minimums of each group's five independently scored dimensions, not averages. Both roles used the same publisher-declared `qwen3-vl-235b-a22b-instruct` model in separate requests, not human reviewers or distinct model families. Public application revision: `eb7f245e2c0d3b573dd8ed6addca9b7f6af26847`. Its declared model, application revision, completed requests, input images and raw responses are recorded. The service's weight bytes were not locally checksum-verified. Blind four-panel image-recognition controls passed in each accepted role execution. No user account credential or billing setting was used or changed.

## Why earlier failed reviews remain in the record

The first surface candidate genuinely needed a more shaped bank and a better snow/earth finish. Those defects were repaired and recaptured before the current source was reviewed.

Some later small-model statements contradicted the actual evidence: white snow was called an empty void, and nighttime/blizzard water was compared directly with the daytime reference palette. The original images, continuous surface geometry, capture conditions and raw failed reports are preserved; those statements were checked rather than adopted as facts. A larger reviewer was verified on blind image controls and then inspected the entire task, not merely the failed images.

The first larger-model review passed 15/16 groups. The remaining night-consistency score was 8.5 despite no listed defect. That score was never rounded, edited or averaged away. A separate clarification request explicitly asked for the reason, not a replacement score; it found no concrete visible inconsistency. Six genuinely new same-camera renders were then captured: clear day, clear dusk, clear night, clear dawn, night blizzard and return to clear day. They keep the camera, terrain and objects fixed. Both night roles were freshly reviewed with all six new frames plus both original night/overview frames; both passed. The two prior night reports, including the previously passing role, remain unmodified in the archive.

Two final reviewer phrases also require qualification: `gallery/snow-workfloor-join.png` is not terrain-only, despite one observation calling it that; the water-state sequence has a fixed camera, despite another observation calling its changes camera jitter. The recorded states and original pixels, not those mistaken phrases, support the verified ground continuity and camera consistency. The raw wording is retained. No mandatory Task 2 surface defect remains identified after this review.

## Exact evidence and reproduction

Build/capture run: `34528232295`.
Original larger-model review run: `34531219636`.
Night-score clarification: `34531677717`.
New controlled capture run: `34532016318`.
Successful combined independent gate run: `34532647994`.

Artifact identities and SHA256 values are in `verified-completion.json`. The downloadable completion bundle contains the complete source-bound captures/tests, both raw role sets including superseded night findings, controlled light-state records, full closure results, local validator, synthetic tests and actual-pixel signoff/adjudications. The exact source is preserved in artifact `10172551654`; no new APK is implied by a source archive.

## Scope and next task

Task 1's approved trees remain preserved and their applicable geometry, visibility and resource behavior checks pass. New tree/model/rig work was not performed. Characters 2-4 final rigging and review remain last.

**Task 3: fences, gates and navigable work lanes — ready, not started.** Tasks 4-47 remain locked behind their predecessors. Any later change that breaks this terrain or the approved trees reopens the affected task before progression.

Native 4K captures are actual software-Vulkan Mobile renders, not sustained physical phone/tablet 60 FPS evidence. Automatic device functionality, complete reference gameplay, unfinished station/NPC artwork, final motion, saves/cloud and all other full-game requirements remain separately unapproved. No unfinished APK or user testing assignment is delivered with this task completion.
