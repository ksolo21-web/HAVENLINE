# Havenline Beta T02 river playtest

T02 brings the approved river into the active World One playtest. The river runs continuously across the 1,024 m playable world. The warm camp floor still appears after purchase, and the west inlet stays accessible. The original ten starter-reach anchors move 25 m away from camp to keep the current perimeter, plots and paid equipment dry. The river follows the original bend and width profile there and extends it into the outer districts.

One level, 3 m wide ice crossing keeps both banks accessible on foot and in the snow truck. Its location uses the existing central crossing reserve. The other two reserves stay clear for future crossings. Roads, fences and new stations were outside this change.

The channel, sculpted shore, collision, placement, navigation and save recovery use the same sampled geometry. The river is 3.39–4.38 m wide across the playable span. The terrain census preserves all 34,794 harvest IDs. It moves 538 sources that intersect the new river corridor onto their original bank and keeps their saved state. The existing camp compass and companion route planner can now find the ice crossing around close bends and from far reaches.

## Reproduced gameplay

- All ten focused Godot suites pass, including all 20 river checks. Coverage includes walking the crossing with touch, impassable open water, level ground underfoot, two dry bank lanes, route clearance and the running water clock.
- A real save from the prior build reopens with owned garage and truck, held wood, truck cargo and a loose world drop. Wet legacy coordinates recover to dry ground on the same side. The real truck prompt mounts the vehicle, drives across the ice and dismounts on dry ground while retaining its cargo.
- Comparison uses recording A at 5 seconds, recording B at 8 seconds and the GitHub forest and frozen-lake render. The native capture pack includes both riverbanks at 1× and 2×, the existing camp and inlet, the crossing, six water samples, a world layout diagnostic and a 3840 × 2160 gameplay frame at render scale 1.0.

The 1,176 m rendered water mesh contains 2,352 triangles. The original 256-triangle terrain note described the 62 m prototype. Current measurements use the playtest's Compatibility renderer with Mesa software OpenGL. Physical hardware testing was skipped at Kaleb's direction for this playtest. Frame resolution and rendering counts are available separately from sustained device performance.

[Source and inherited T01 review](Candidate.json) · [Reference source identities](Reference/Reference-provenance.json) · [Paired reference images](Reference/Locked-reference-and-owner-biome.jpg) · [Gameplay at native 4K](Capture/native-4k-bank.jpg) · [Full world layout](Capture/diagnostic-plan.jpg) · [Regression results](Tests/results.txt)

Implementation and integration review by Codex. Independent reference review by the independently assigned T02 reviewer.

## Independent review

C1 scored 10/10 in each of its three visual dimensions. C2 scored 10/10 in each of its four geometry dimensions. The review applies to T02 terrain, shoreline and crossing at the frozen source. It leaves the T01 scores and the separate workload evaluation as recorded. The cold save test and 16 full camp guide traces were also rerun on the final source after the review captured its evidence.

[Independent review](Review/Exact-060d4c76-review.md) · [Side-by-side comparison](Review/Azure-match-board.jpg)
