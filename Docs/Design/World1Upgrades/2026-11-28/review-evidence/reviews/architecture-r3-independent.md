# Havenline architecture r3 — independent review

**Verdict: rejected; foreground rails still missing. Architecture-only score: 7.5/10.**

All 12 original checks pass; both regression gates remain failed (12/14 mandatory checks passed). The applicable exact-10 reference gate is not met. This is a static unarmed architecture review; it does not clear the owner’s armed-attack requirement or any runtime task.

## Exact evidence

- Candidate: `/workspace/scratch/9a64cbeeb049/world1-upgrade-expansion/generated/w1val-02-architecture-r3.png`
- Candidate SHA256: `54680cb395f36015e1a29b8ca35ab998035dcc0c460fe7a0a2005817ae694aaa`
- Exact invocation SHA256: `fc243fe9d18a03b7ba36c28ca6972983435301f15ca7e99c21d04ed0eb3dba42`

The full six-panel image and four interior/access closeups were actually inspected. All three original family-source hashes and the r2 edit reference match their previous records. Inspection crops do not alter the candidate.

## Remaining defects

**AR-03 remains open.** GUARDWALK INTERIOR has no foreground rail where ACCESS shows continuous raised rails. FORTIFIED LOOKOUT now has the main-walk foreground rail in ACCESS, but the corresponding INTERIOR edge remains only partly protected. The views still differ structurally.

**AR-04 remains open.** GUARDWALK INTERIOR exposes the full foreground deck/walk perimeter. Both FORTIFIED LOOKOUT interior/access views omit the rail between the foreground roof posts along the blue-trimmed deck edge. The adjacent main-walk span in INTERIOR has only a floor-level strip, not the raised low rail shown elsewhere.

## Minimal spatial repair

Coordinates are approximate **[left, top, right, bottom]** pixel bounds in the original **1536 × 1024** image, with the origin at the upper left. Target the edges nearest the viewer, not the existing background rails.

| Target | Panel | Pixel bounds | Action |
|---|---|---|---|
| P01 | GUARDWALK INTERIOR | `[542, 207, 862, 278]` | Add a raised low rail along the FOREGROUND floor lip, from the left deck corner through the middle support post to the LEFT stair-top post. Raise or extend the posts as needed; stop before the stair opening. This is the empty edge nearest the viewer, below the visible walking floor, not the rail already along the back. |
| P02 | FORTIFIED LOOKOUT INTERIOR | `[542, 655, 678, 716]` | Add the low rail BETWEEN the two FRONT roof posts above the blue-trimmed deck edge. It runs horizontally across the front of the roofed platform and protects its outside edge. |
| P03 | FORTIFIED LOOKOUT INTERIOR | `[675, 673, 790, 728]` | Continue a proper raised low rail from the right FRONT roof post to the existing near walkway rail. The floor-level decorative strip must not substitute for a raised protective rail. |
| P04 | FORTIFIED LOOKOUT ACCESS | `[1345, 626, 1447, 699]` | Add a low rail BETWEEN the two FRONT roof posts directly above the diagonal blue-trimmed outer deck edge. Continue the existing foreground walkway perimeter into this outer roofed-deck span; do not rail across the internal entry at the deck side. |

Preserve both stair openings, the flush internal deck connection, raised lookout posts, headroom, supply alcove, single-level Guardwalk and all existing materials and labels. Do not install any partition across the internal walk-to-lookout passage.

## Retest results

| Gate | Result |
|---|---|
| A01: Actual candidate, exact prompt and all supplied source images inspected | PASS |
| A02: Six panels with exterior, opposite interior and high access views for both stages | PASS |
| A03: Source material/palette/snow family preserved within explicitly authored geometry adaptations | PASS |
| A04: Substantial architectural silhouette/material progression rather than recolor only | PASS |
| A05: Staircase to open landing to main walkway is readable in both stages | PASS |
| A06: Guardwalk observation platform continuously accessible and visibly usable | PASS |
| A07: Fortified lookout has unambiguous walkway entry and occupied-space clearance | PASS |
| A08: No new gate, wall doorway or extra camp entrance shown | PASS |
| A09: Closed supply crates/alcove and empty observation equipment scope retained | PASS |
| A10: No weapons, ammunition, combat, targets, injuries, stats or level claims | PASS |
| A11: Objects fully framed; labels are readable and geometry is inspectable | PASS |
| A12: Meaningful full-frame plus interior/access closeups actually reviewed | PASS |
| R01: Repair preserves a consistent physical rail layout across exterior, interior and access views | FAIL |
| R02: Exterior occupied deck edges retain low protective rails; only internal connector and stair-top entry are open | FAIL |

## Raw dimension scores

| Dimension | Score |
|---|---:|
| Reference material and style family | 10.0 |
| Silhouette progression | 10.0 |
| Cross view stage identity | 8.0 |
| Framing and label readability | 10.0 |
| Stair landing walkway readability | 10.0 |
| Observation platform access | 10.0 |
| Occupied space clearance and entry clarity | 10.0 |
| Outer edge protection and rail layout | 7.5 |
| Limited scope truthfulness | 10.0 |

The two original access defects remain closed for static concept readability. Exact world dimensions, native collision/pathfinding, combat behavior, animation, audio, device and shipping evidence remain untested. Preserve this rejection and repeat all 14 checks on the actual repaired image.
