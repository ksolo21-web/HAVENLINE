# Havenline Level 1 Android playtest

Android ARM64 build 7 runs `res://field_opening.tscn` from game commit `ec989c640233e71ee86dd57e43076e2e932d612a` on `trial/world-one-expansion-2026-11-26`. The previous playable was `3ce0414d667d18533a110fa0f3770bb8647dacb3`. The archive below belongs to the trial, with gameplay recorded using isolated test profiles.

[Private Android download](https://havenline-level1-android-playtest.ksolo21.chatgpt.site/Havenline-Level-1.apk) · [Game source](https://github.com/ksolo21-web/HAVENLINE/tree/ec989c640233e71ee86dd57e43076e2e932d612a/HavenlineLevel1) · [Signed package details](Verification/Android.json) · [Download verification](Verification/Private-download.json)

## Playing the update

Open the existing test app after installing the update. Drag anywhere on the field to run and pinch to zoom. Outside camp, the orbiting tool gathers and attacks automatically. Bring materials close to the printed edges to pay for construction. Tap the graphics control to change quality.

The starter furnace, perimeter and gates appear on the first paid plot. After the second expansion, the cooker, saw bench and drill each require payment. The cooker costs 120 wood and 80 stone, the saw 140 wood and 60 stone, and the drill 100 wood and 120 stone. Existing purchases, partial production and customer receipts carry forward. Purchase and rescue the survivor to see the companion at work. The survivor gathers local timber and stone, picks up loose supplies, feeds purchased machines, helps pay a construction bill the player has started, and serves the next customer's meal. Each of the six raw material families has its own 500-unit worker limit.

## Footage for Alfred

| What to inspect | Recording or comparison |
|---|---|
| Fresh snow, final wood payment, furnace, south and east gates in both directions | [Continuous touch playthrough](Transfers/Furnace-and-both-gates.mp4) and [crossing times](Transfers/Furnace-and-both-gates.json) |
| Character 1 run and contact | [Build 6 and Build 7 in motion](Run/Character1-run-comparison.mp4) and [independent rig review](Rig-review/Reference-and-verdict.md) |
| Owl and enemy AI | [Owl guarding the east gate](Combat/Gate-defense.mp4) and [mixed pack at pinch zoom](Combat/Mixed-pack-2x.mp4) |
| Purchased equipment and processing | [Three powered workshops](Machines/Independent-review/Three-paid-workshops.mp4) and [independent art and purchase review](Machines/Independent-review/Independent-machinery-review.md) |
| Worker delivering food and charging a customer | [Worker sale](Workers/Worker-serves-a-customer.mp4) and [capacity and job tests](Workers/README.md) |
| Phone HUD and side-entry reveal | [Before and after](HUD/Reference-HUD-review.jpg) and [reference and revised reveal](HUD/Side-final/Reference-and-two-reveals.jpg) |

## Validation

The frozen playtest rig scored **8.8/10**. Its maximum steady gap beneath both boots dropped from 99 mm to 34 mm. The independent reviewer found visible compression at the rear boot cuff when braking. Of 1,328 required rig checks, 16 remained open. The locked diagonal reference and the faster lateral reference establish different travel speeds. See [the failing pose](Rig-review/Game/Native-braking-cuff.jpg) and [exact rig verdict](Rig-review/Reference-and-verdict.md).

The native regression run included 43 suites in 46 processes. See the [full results](Verification/Native/Native-results.json), [16-process Level 1 progression and restart test](Verification/Completion/Completion-results.json), [signed payload save-upgrade test](Verification/Signed-save-upgrade.json), [rig review](Rig-review/), and [reference/tradeoffs for the production team](Team-reference-notes.md). The two Ultra images were rendered at 2160 × 3840 with internal 3D scale 1.0 in the Godot software renderer. See the [normal gameplay view](Verification/Ultra/Ultra-1x.jpg) and [2× pinch view](Verification/Ultra/Ultra-2x.jpg). The native device list was empty. Physical Fold7 smoothness, 4K at 60–120 fps and exact frame-for-frame run equivalence remain unverified. The original sampled views periodically obscure the boots. The equipment and owl use Havenline's own art, mechanics and balance.

The three textured workshop generations cost 45 Meshy credits in total. [Source sheets, asset hashes and expenditure](Machines/Models.json)
