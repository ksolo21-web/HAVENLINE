# Character 1 gameplay review

**Character 1 passed the requested 9.5/10 minimum in the Level 1 opening.** The independent critic scored the final trial build against the compact mittened Character 1 turnaround and the locked gameplay reference frames.

| Criterion | Previous | Reviewed |
| --- | ---: | ---: |
| Match to the character and gameplay references | 9.25 | **9.50** |
| Visual language | 9.50 | **9.75** |

The blue parka and orange trim now read more clearly at gameplay distance. Twelve mixed-resource packets span 36 pixels across the character’s back in the matched walking frame, down from 65. All twelve remain visible. Each resource stays with its own kind. The timber faces outward with the bark visible. Its center seam and maximum stack height still differ from the reference. The available reference frames also leave the exact footfall cadence unresolved. Both visual criteria remain open under the project’s separate 10/10 art rule. [Independent review](Critic/Review.md) · [Recorded scores](Critic/Scores.json) · [Criterion verification](Critic/Criterion-check.json)

## Watch and play

- [Updated gameplay](Gameplay/Character-1-gameplay.mp4) and [previous gameplay](Gameplay/Previous-build-gameplay.mp4) show the same movement from the fixed gameplay camera at normal and 2× zoom. Each silent clip lasts 5.67 seconds. The loaded shots stage two of each of the six resource types for comparison.
- [Before-and-after frames](Gameplay/Before-and-after.jpg) show the empty character, loaded walk, turn and stop. The [timber comparison](Critic/Loaded-silhouette.jpg) includes the source reference.
- [4K empty](Gameplay/Character-1-default-4k.jpg), [4K loaded](Gameplay/Character-1-loaded-4k.jpg) and [4K loaded at closest pinch](Gameplay/Character-1-loaded-pinch-4k.jpg) are native 3840 × 2160 software-rendered stills. Physical phone performance at 60 or 120 fps remains unverified.
- [Linux playtest](Play/README.md) · [Rebuild from Git](Source/README.md)

## Verification

A separate fresh-profile playthrough earned all eight purchases, conserved resources at every tick and crossed both gates in each direction at all three perimeter sizes. The automated regression run passed 22 suites across 23 invocations with zero reported errors or warnings. Collision checks found no cargo entering the character in 416 sampled poses and no orbiting tool entering cargo across 5,184 tested configurations. [Earned playthrough](Gameplay/Earned-route.json) · [Regression and rig audit](Regression/README.md) · [Skinned-body clearance](Regression/Geometry/Body-and-pack.json)

The report covers Character 1. The gameplay capture and Linux package use commit `92d5aebe1740d0d7beebdc1f6b01ffbcf0604736`. The final reviewed commit is `37540b6d1d6e0657dd6776db136a46534e6a66d5` on `trial/world-one-expansion-2026-11-26`, scene `res://field_opening.tscn`. Its two additional changes affect export-excluded test fixtures. The independent critic rerendered the final commit and reproduced all 12 empty-pack views and 24 load projections. All test saves used isolated profiles. Meshy credits used for this correction total zero. [Final source replay](Critic/Final-source-equivalence.json) · [Package verification](Play/Final-source-compatibility.json)
