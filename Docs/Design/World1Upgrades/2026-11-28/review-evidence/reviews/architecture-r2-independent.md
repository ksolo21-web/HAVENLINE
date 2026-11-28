# Havenline architecture r2 — independent review

**Verdict: rejected; rail regression repair required. Architecture-only score: 7.5/10.**

The two original access defects are repaired. All 12 original inspection gates now pass, but both additional regression checks fail (12/14 total). This cannot pass the applicable exact-10 reference gate. Scores are not averaged and missing native evidence is not inferred.

This review covers only a static, unarmed protective-architecture concept. It does not approve the owner’s armed-attack illustration, the full defense task, or any runtime implementation.

## Exact candidate

- Candidate: `/workspace/scratch/9a64cbeeb049/world1-upgrade-expansion/generated/w1val-02-architecture-r2.png`
- SHA256: `f96b28288243f26e7e38ec1493f278abfa0ea11c5ad81db2f71698277ba79d44`
- Invocation: `/workspace/scratch/9a64cbeeb049/world1-upgrade-expansion/prompts/w1val-02-architecture-r2-invocation.json`
- Invocation SHA256: `61577a9a4292425b156db22527895fbee8c657ab856b0f8d677df21fbdf2fc19`

The r1 edit reference remains unchanged. All three original family source images were actually viewed in this critic’s r1 review; their hashes were rechecked and match. The entire r2 sheet and four meaningful interior/access closeups were reviewed. Inspection crops only enlarge the image for review and do not alter the candidate.

## Findings

**AR-03 — inconsistent rail layout.** GUARDWALK INTERIOR removes the entire camp-side outer rail, while ACCESS retains the rail along that edge. FORTIFIED LOOKOUT INTERIOR includes one short near-edge rail segment near the stair end that ACCESS omits. These panels depict different physical rail layouts; none is labeled as a cutaway.

**AR-04 — exposed outer drop edges.** The repair opens much more than the internal walkway-to-observation connection. GUARDWALK INTERIOR leaves the observation deck and walk’s camp-side outer edge unprotected. FORTIFIED LOOKOUT INTERIOR and ACCESS leave the roofed deck’s camp-side edge and substantial main-walk edge unprotected. The exact prompt retained low rails on other deck edges.

**Required repair:** restore a single, consistent low perimeter rail layout in all three views. Keep only the stair-top entrance and the internal walk-to-deck connection open. Retain the current flush single deck, tall lookout posts, clear entry, main stair and separate ground supply alcove. Do not remove outer rails merely to expose the route; the high access view can show it.

## Original repairs confirmed

- AR-01 closed for static concept: the inaccessible upper equipment pedestal/socket is gone, and the walk connects directly to one flush observation floor.
- AR-02 closed for static concept: the later lookout has a broad open entry, flush floor and visibly raised roof posts. Exact native headroom, dimensions and pathfinding remain untested.

## Scores

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

## Mandatory gates

| Gate | Check | Result |
|---|---|---|
| A01 | Actual candidate, exact prompt and all supplied source images inspected | PASS |
| A02 | Six panels with exterior, opposite interior and high access views for both stages | PASS |
| A03 | Source material/palette/snow family preserved within explicitly authored geometry adaptations | PASS |
| A04 | Substantial architectural silhouette/material progression rather than recolor only | PASS |
| A05 | Staircase to open landing to main walkway is readable in both stages | PASS |
| A06 | Guardwalk observation platform continuously accessible and visibly usable | PASS |
| A07 | Fortified lookout has unambiguous walkway entry and occupied-space clearance | PASS |
| A08 | No new gate, wall doorway or extra camp entrance shown | PASS |
| A09 | Closed supply crates/alcove and empty observation equipment scope retained | PASS |
| A10 | No weapons, ammunition, combat, targets, injuries, stats or level claims | PASS |
| A11 | Objects fully framed; labels are readable and geometry is inspectable | PASS |
| A12 | Meaningful full-frame plus interior/access closeups actually reviewed | PASS |
| R01 | Repair preserves a consistent physical rail layout across exterior, interior and access views | FAIL |
| R02 | Exterior occupied deck edges retain low protective rails; only internal connector and stair-top entry are open | FAIL |

## Evidence and limits

The JSON report binds the exact source and candidate hashes and records the raw findings. `architecture-r2-crop-evidence.json` records the four source crop coordinates and inspection-only enlargement.

No weapon, ammunition, combat, target, injury, numerical stat or level claim appears on this sheet. Its unarmed scope stays explicit. Armed attack capability illustration, native collision/pathfinding/dimensions, defense values, behavior, animation, audio, device and shipping evidence remain outside this limited review.

Preserve this rejection and retest all 14 checks after repair. Do not use the original 12 passes to conceal the new failures.
