# Havenline Level 1 Android playtest 8

[Download the private Android APK](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/Havenline-Level-1.apk) · [Source at fbbbca916b](https://github.com/ksolo21-web/HAVENLINE/tree/fbbbca916baa2d73e0f30b66a075ad7076e61dac/HavenlineLevel1) · [Signed package](Verification/Android.json)

This build runs `res://field_opening.tscn` on the existing trial branch. Drag anywhere on the field to run and pinch to zoom. The orbiting weapon activates outside the paid camp. The owl can intercept wolves outside either gate, including while the player stands in safety near the opening.

**Character 1 passed the independent rig and gameplay review at 9.5/10.** All 1,392 required checks passed across 64 joints and four clips. The recovered fleece keeps its shape through flex and braking. The maximum gap under both soles fell from 9.9 cm in Build 6 to 3.4 cm, with nine real landings producing nine prints in the author's route. Planted boot material travels 1.9–3.3 cm. The diagonal matches reference A's observed pace. The lateral B passage is 15–20% faster. Internal garment intersections were still measurable; the reviewers found continuous clothing from the gameplay camera at both zooms. [Independent review](Rig-review/Reference-and-verdict.md) · [Physical landings and movement](Run/Run-review.md) · [Signed character resource](Verification/Signed-character.json)

## The camp loop

Approach an accessible plot edge carrying the requested supplies. Partial payments survive a departure or restart. Pay for the furnace and camp, then expand, build the storage house and expand again. The cooker costs 120 wood and 80 stone, the saw bench costs 140 wood and 60 stone, and the quarry drill costs 100 wood and 120 stone. Each machine becomes available in turn and runs unattended once purchased and fed. The rescued survivor can supply the machines, finish a plot payment the player started and serve a customer's meal. Each of six raw materials has its own 500-unit survivor limit.

The per-task audit covers T01 through T11 and separates native Level 1 results from open production requirements. [T01–T11 audit](T01-T11-audit.md)

## Footage for Alfred

| What to inspect | Evidence |
|---|---|
| Snow before purchase, final payment, furnace, both gate crossings each way and automatic orbit | [Continuous gameplay with sound](Transfers/Furnace-and-both-gates.mp4) · [Crossing times](Transfers/Furnace-and-both-gates.json) |
| Character 1 on open snow and through braking | [Landings, turns and reference footage](Run/) · [Independent rig evidence](Rig-review/) |
| Gameplay camera at default and double pinch zoom in Ultra | [2160 × 3840 at 1×](Verification/Ultra/Ultra-1x.jpg) · [2160 × 3840 at 2×](Verification/Ultra/Ultra-2x.jpg) |
| Cooker, timber saw and quarry working after separate payments | [Workshop gameplay and review](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/Machines/Independent-review) |
| Owl intercepting a wolf at a gate and engaging an alpha | [Combat clips](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/Combat) |
| Survivor carrying all six categories, delivering supplies and completing a customer order | [Worker sale and capacity checks](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/Workers) |
| Covered and unfolded HUD, interrupted payment and furnace warmth sequence | [HUD and reveal](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/HUD) |

## Verification

43 gameplay suites passed in 46 native runs. Another 217 checks covered progression, interruptions and cold restarts. The signed package preserved Build 6 and Build 7 saves in isolated profiles. The mixer played 56 sound effects and three music states. Ultra stills were rendered at full internal resolution on desktop. Physical Galaxy Z Fold7 frame pacing at 60–120 fps remains unmeasured. [Regression results](Verification/Native/Native-results.json) · [Level 1 progression](Verification/Completion/Completion-results.json) · [Signed save tests](Verification/Signed-update.json) · [Private APK download check](Verification/Private-download.json)

Build 8 revises Character 1's skin and clip data. All other 515 gameplay source and asset hashes match the preceding playtest. The paid workshops used 45 Meshy credits in Build 7. The cuff repair used the original fleece geometry and textures. [Exact changes](Verification/Changes-from-Build7.json) · [Asset generation records](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/Machines/Models.json) · [Reference and rigging research for the team](https://github.com/ksolo21-web/HAVENLINE/tree/c6921b931265fe54dcc572f7a64078717c394abc/Docs/QA/Grounded-Camp-2026-11-27/Team-reference-notes.md)
