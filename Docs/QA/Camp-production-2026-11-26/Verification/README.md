# Procedure and results

The source under review is `30524e3da7906e252e1de7dd4529250b060868be`, scene `res://field_opening.tscn`, Godot 4.7.2. The trial and every test used isolated saves. The Native and Completion runners verified all 357 reviewed inputs before and after their runs.

| Check | Result |
| --- | --- |
| Existing native regression | 27 suites passed in 28 launches. [Native report](Native/Native-results.json) |
| Completion, clearance, migration and interrupted writes | 210 assertions passed across 16 fresh processes. Four simulated failed writes preserved the prior durable payload. [Completion report](Completion/Completion-results.json) |
| Hopper, raw inventory and migration | 15 balance checks passed. [Domain checks](Balances.log) |
| Automatic survivor supply | 47 checks across pickup, cold restart, successful delivery and a full hopper. [Trip checks](Worker-and-storage.json) |
| Linux package | 12 checks against the pack embedded in the exported executable. The actual packaged launcher also opened, accepted a physical key press, saved the movement and closed normally. [Packed-scene assertions](Packaged-Scene.json) · [Native launcher](Linux-launch/Linux-launcher-and-movement.json) |
| Android package | Signed ARM64 debug APK. All archive members passed their CRCs, all local/central filenames matched, Android signature verification and 16 KiB alignment passed. Hardware performance remains unmeasured. [APK inspection](Android.json) |
| Fixed-camera tower occlusion | A triangle test identified 149 affected baseline torso samples. The correction exposes the character across the same route while preserving the tower away from the player. [Before](Tower/tower-occlusion-before.json) · [After](Tower/tower-occlusion-after.json) · [Pixel comparison](Tower/pixel-verification.json) |
| Independent visual review | Six of six criteria met 9.5/10. [Scores and observations](Independent-review.md) · [Frame and audio inspection](Film-inspection.json) |
| Independent route | Separate controller replay from the earned checkpoint with ordinary movement, intake, machine operation, pickup, payment and survivor supply. [Position and balance checks](control-proof.json) |

The full completion suite, balances and worker supply scripts are in the reviewed game’s `tests` directory. Native tests exercise the individual interactions in an isolated profile. The film shows the fixed gameplay camera and the movement between interactions. The intended 4K and 60–120 Hz device target requires a phone or tablet measurement. [Recorded route](../Gameplay/README.md) · [Source extraction](../Source/README.md)

The existing T01–T11 register tracks the wider Level 1 production requirements, including which tasks still need visual reapproval. [Level 1 task audit](https://github.com/ksolo21-web/HAVENLINE/blob/f55128d744d3ac610dc6667673c9d040770a9da2/Docs/QA/Level-1-Settlement-2026-11-26/Audit/README.md)
