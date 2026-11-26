# Level 1 regression results

The ordinary gameplay scene `res://field_opening.tscn` passed 27 native suites across 28 top-level runs. The completion and recovery test passed 158 checks across 12 separate Godot processes. Both runners verified all 343 source-manifest entries before and after their runs. Every process exited successfully with zero reported Godot warnings or errors.

| Test | Result |
| --- | --- |
| Old save and unpaid plot | 52 checks passed |
| Rescue, real wood token and banked delivery | 38 checks passed |
| Cooking and paid FIFO service | 19 checks passed |
| Two processors and live owl contact | 14 checks passed |
| Touch handoff and cold relaunch | 35 checks passed |

Three deliberately failed save writes left the previous durable bytes unchanged. Retrying the real worker deposit, currency grant and Level 2 transition produced exactly one receipt each. The actual chapter on relaunch read **Level 2 · Preview**. The player could continue in the snowfield, and the gameplay HUD showed cash, both workshop balances and live HP.

The wave test ran 200 waves with 572 enemies, 31 alphas, 0 duplicate drops and 0 orphaned wolves. The snowfield test verified all 1024 populated chunks against the shipped map and identified 22 original resource positions inside the new lake and workshop footprints. Fresh-process ordinary travel restored the same world position within 0.000 m, HP 3 and a 8.25-second running cooldown.

The migration test used prior source `37540b6d1d6e0657dd6776db136a46534e6a66d5` to write its version-3 profile. It supplied the original eight camp receipts and raw resources through the inventory API. The focused tests positioned the player at the real interactions and injected a save lock at selected commits. The gameplay footage documents ordinary input separately. Each test used a private save home. Four additional launches verified the prior native store and the new game's native application directories, including a write and read in each. Each sibling's saved bytes stayed unchanged. The Level 2 result covers the preview handoff and continued play in the existing world. No Android device was attached for hardware performance verification.

Reviewed source `a0e83999064b666145a884eed767f68d4d127688` using Godot `4.7.2.stable.official.ed1daf0bf`.

A separate normal window-close test ran the gameplay scene for 140 native physics frames, sent the real window close signal and exited cleanly. [Window-close log](normal-window-close.log)

[Native suite logs](Native/Native-results.json) · [Completion receipts](Completion/Completion-results.json) · [Native application directory checks](Directories/Directory-results.json) · [Device inventory](ADB-devices.txt)
