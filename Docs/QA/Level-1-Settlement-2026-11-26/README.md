# Havenline Level 1 settlement trial

**The ordinary Level 1 route passed from a fresh profile.** In 264.40 seconds of simulated play, Character 1 earned eight camp purchases, bought the separate survivor plot, harvested with the owl, processed wood and stone, and sold a cooked meal across the north fence. The 39.71-second reel shows the key events at gameplay speed with the native stereo mix. A separate process reopened both the ready checkpoint and the saved Level 2 preview. [Watch the gameplay with sound](Gameplay/Level-1-completion.mp4) · [Chapter times and game receipts](Gameplay/Gameplay-QA.md) · [T01–T11 audit](Audit/README.md)

The tested scene is `res://field_opening.tscn` in Godot 4.7.2 on `trial/world-one-expansion-2026-11-26`. The reviewed gameplay commit is `a0e83999064b666145a884eed767f68d4d127688`. The source manifest lists 343 verified inputs. [Gameplay commit](https://github.com/ksolo21-web/HAVENLINE/commit/a0e83999064b666145a884eed767f68d4d127688) · [Verification and build instructions](Source/README.md)

## What Alfred can test

| In the game | Observed result |
| --- | --- |
| Build the first camp and cross its perimeter | The purchase built the centered furnace, fence and gates. The recorded route made 16 open-gate crossings and covered both gates in both directions at all three perimeter sizes. Snow tracks continued outside. [Before](Gameplay/Stills/the-unpaid-opening.jpg) · [After](Gameplay/Stills/the-first-paid-camp.jpg) · [Crossing times in the film](Gameplay/Evidence/Both-gates-in-both-directions.json) |
| Buy the survivor plot | Two carried wood pay for one plot. Rescuing the worker and opening wood storage starts the two-handed chopping and haul. The worker deposited 8 distinct wood bundles on the recorded route. [Worker evidence](Survivor/worker-audit.json) |
| Hunt with the owl | The paid plot unlocks the owl. It takes off outside camp and returns to its perch in safety. Its talons landed 2 recorded hits on live enemies. [Owl at the east gate](Gameplay/Owl/Owl-in-Level-1.mp4) |
| Use the saw, quarry drill and cooker | The saw cut 1 plank bundle and the quarry produced 2 dressed blocks. The cooker used one carried meat and prepared one roast. [Workshop comparison](Gameplay/Shore-workshops/Workshop-reference-and-gameplay.jpg) |
| Sell the roast across the north fence | Customers queued on the snow side of the timber counter. Character 1 served from inside, the buyer passed a bundle of notes, the HUD showed Cash 1, and the next customer advanced. All ten collision sweeps at the counter and fence joints were blocked. [Counter and trade](Counter/README.md) |
| Read the HUD and continue | The HUD shows HP, cargo, work progress, workshop outputs, cash and the current objective. The fully earned **Preview Level 2** button saves a trial continuation in the same snowfield. The production Level 2 unlock remains a T12/T32 design decision. [Progression authority](References/Progression-authority.md) |

## Verification and remaining work

The final build passed **27 native suites** in 28 launches, plus **158 checks** across twelve cold starts covering save migration, blocked receipts, paid progression and reload. The Linux package passed all 23 asset and audio comparisons and an actual window, movement, save and exit test. The ARM64 Android debug trial passed signing, alignment, packaging and launcher checks. Both packages use dedicated trial storage. [Native regression](Regression/Native/Native-results.json) · [Transaction and restart checks](Regression/Completion/Completion-results.json) · [Playtest packages and controls](Play/README.md)

The returning field checks also passed for five-second tree and mineral regrowth, separate carried and stored materials, gate and camp safety, snow tracks, the threat-side tower, player damage and respawn. The encounter stress test handled 200 waves and 572 enemies, including 31 alphas, with zero duplicate drops or orphaned wolves. [Field and encounter results](Regression/Results.md)

The independent critic scored all ten assessed settlement features at least **9.5/10**. The T01–T11 audit names the evidence for each task. The production register still flags T03, T04, T05, T08, T09, T10 and T11 for visual reapproval. The working cooker uses the recovered T05 station. The original reviewed V18 binary and the original audio track for reference B are still unavailable for direct comparison. The 4K stills show image quality at both zooms. Sustained 60–120 fps on a physical device remains unmeasured. [Independent scores](Audit/Scores.json) · [Native 4K views](Gameplay/Ultra/README.md)

Meshy spend was zero. All recorded runs used isolated test profiles.
