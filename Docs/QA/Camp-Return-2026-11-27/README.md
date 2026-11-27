# Havenline · Camp return playtest

**Android build 6, version 0.3.5-camp-return.** The playable field is `res://field_opening.tscn` in `HavenlineLevel1` at `3ce0414d667d18533a110fa0f3770bb8647dacb3`. The previous signed build was `8a8768438b3e9215a44f34e71a06cc54a55890f6`. [Download the Android update](https://havenline-level1-android-playtest.ksolo21.chatgpt.site) · [Phone controls](Play/README.md)

## What happened in build 5

An empty-save run earned timber and stone, built the starter storehouse and found that reinforcement worked only at the side of the loading apron. Both subsequent house tiers hid the priced construction marker. A hurt player reached camp at 10/30 HP and stayed injured. The run held opposing boots extended before switching support. Interrupting a touch drag with an application pause also left the stick held.

## Changes and checks

| Area | Build 6 result |
| --- | --- |
| Construction | The storehouse entrance accepts stock. A separate priced floor tile accepts reinforcement and advanced-tier payments. The HUD identifies the next construction project, shows the remaining price and points to it. A new approach is required to start the next tier. |
| Save continuity | An isolated save written by the signed build 5 contains partial reinforcement, carried wood and stone and stored wood. Actual touchscreen steering in the signed build 6 content finishes that upgrade from both balances. Reopening retains the house tier and next offer. |
| Safe return | The compass leads to the starting plot before the first purchase, then around the paid perimeter and lake to an active gate. A tester followed only the compass from 101 m away. An injured character recovers 3 HP per full second inside paid camp, up to 30. Leaving interrupts the current pulse. |
| Mobile input | Interrupted steering, pinch and HUD contacts clear on application pause, focus loss and viewport resize. The same touch ID steers again on return. |
| Level 1 ending | Construction stops after all eight receipts. The objective moves to remaining survivor, owl, processor or customer work. A paid north-counter meal unlocked Continue in a late-game playthrough. Tapping it entered the Level 2 preview and a second launch retained that state. |
| Character 1 | The new field run uses separate leg recovery and support timing, continuous arm swing and a torso lean into turns. The maximum run speed remains 7 m/s. Review footage covers both zoom levels and loaded and unloaded runs. |

## Reviewer verdicts

The independent reviews scored the run 9.5/10, the storehouse upgrade 9.5/10, the return guide 9.6/10 and healing feedback 9.6/10. At 2× from the west the hearth can cover one floor bracket. A tall load can hide the far glove and boot briefly from a rear angle. Full-build performance certification and the separate T01–T11 audit are outside this playtest verdict.

## Reproduction and evidence

The source manifest binds 460 reviewed inputs to the game commit. The clean Godot import now includes the forester pine’s six original texture dependencies at import time. The APK has the same application ID and signer as build 5. The private server returned the full signed file with SHA-256 `5e893c6f163d83d4a782eed0e5503a4587a9cf99a7936120533c5688eef5aa48` and served a valid byte range.

The native regression runner passed 39 suites over 42 launches. The completion runner passed 208 checks across 16 launches. It exercised the survivor, cook, machine, counter, customer payment, cancellation, recovery and level-preview flows across separate launches. Its verification-only commit `670c17de470f9d9b2037911390b3f8fb1fd29e7f` updates a single assertion which still expected the former post-completion hint. The new assertion checks the visible “All Level 1 plots complete” message after a cold launch. Every shipped game file matches the APK revision. The full run and save update used isolated profiles. Gameplay captures used Linux Godot and a software renderer. Physical Galaxy Z Fold7 performance, installation and 4K frame timing remain unmeasured.

- [Android package verification](Verification/Android.json)
- [Signed-build compass width](Verification/Signed-compass.json)
- [Motion review binding on the shipped source](Verification/Motion-review-binding.json)
- [Signed game controls, camp crossings and save migration](Verification/Signed-game-and-save.json)
- [Full fresh and returning playthroughs](Verification/Journey-audit.json)
- [Native regressions](Verification/Native/Native-results.json)
- [Level completion regressions](Verification/Completion/Completion-results.json)
- [Pinned source and scene](Source/Reviewed-files.json)
- [Private APK download verification](Verification/Private-download.json)

## Gameplay footage

- [Character1 run comparison](Views/Character1-run-comparison.mp4)
- [Upgrade return and healing](Views/Upgrade-return-and-healing.mp4)

## Review

The animation builder was production_runtime. The independent rig and camera reviewer was production_qa. The independent field playthrough and reference reviewer was production_capture. The gameplay comparison and review records describe the inspected scope.

- [Journey visual review](Verification/Journey-visual-review.md)
- [Character1 run review](Verification/Character1/Character1-run-review.md)
- [Review](Verification/Independent-critic/Review.md)
