# Havenline Task 3 — frozen fences, gates and navigable work lanes

## Status

Task 3 is ACTIVE. Task 4 and later tasks stay locked until this scope passes mechanical/regression checks, the cheap performance-budget preflight, the formal source-bound river-gate evidence preflight, both independent critic roles at >9.0 in every applicable mandatory dimension, the full C6 Performance Critic, and final pixel signoff. Target is 10/10.

The strict `>9.0` rule is forward-only from T03. Prior T01/T02 approvals are not retroactively revoked.

Accepted prerequisites remain authoritative:

- T01 approved conifers/forest framing must not regress.
- T02 accepted gameplay source `1f0ba3bede3d160a34751c2fcdbfa78c1b6785ff` and `river_v1_mapspan` geometry remain fixed.
- Current movement bounds stay X=-14.2..14.2, Z=-16.2..16.2.
- No bridge is added in T03. The three Task 2 future crossing corridors remain open.

## Visual language

Use the existing authored winter kit, not primitive blocks. Static camp fencing is built from the authored `environment_v2/barricade.glb` (irregular split timber tops, cross braces, forged straps and snow crowns). Gate thresholds use the authored `environment_v2/lantern_post.glb`, with paired open timber leaves made from the same barricade art. Source GLBs are never modified.

The result should read like the fenced warm/brown winter work area in the authoritative reference video: a clear protected camp perimeter with deliberate openings and obvious walkable circulation, while keeping Havenline’s approved river and blue-white forest.

## Locked perimeter

The permanent camp perimeter is on the NORTH bank.

- East/west side fence nominal X: +/-12.4.
- North fence Z: +8.8.
- South fence follows the accepted river’s north-bank curve at exactly the permanent-build setback: local shore distance = `WET_EDGE + BANK_RUN + SNOW_SHOULDER + BUILD_SETBACK` (3.05 world units).
- Fence visuals and fence collision are generated from the SAME segment list.
- Fence collision actor radius: 0.32 world units.

### Gate openings

All openings are real collision gaps and visually marked with lantern posts plus open timber leaves.

1. North main gate: center (0.0, +8.8), clear width 3.6.
2. West work gate: side X=-12.4, center Z=+2.4, clear width 3.4.
3. East work gate: side X=+12.4, center Z=+2.4, clear width 3.4.
4. West river gate: centered on Task 2 crossing reserve X=-9.0, clear width 3.4 measured along the south fence.
5. Central river gate: centered on Task 2 crossing reserve X=+1.5, clear width 3.4.
6. East river gate: centered on Task 2 crossing reserve X=+10.0, clear width 3.4.

The three river-facing openings must preserve at least the Task 2 reserved 3.0-unit collision/crossing corridor. Posts and open leaves must also preserve a separate minimum 3.20-unit visual aperture after leaf projection so a technically open gate cannot pass while looking cramped or obstructed. No permanent fence panel may cross the reserves.

Where practical, the same authoritative T03 gate contract must drive visible gate geometry, collision-gap assumptions, route reservation/apron geometry, and evidence metadata. A repair may not move only the visible leaf while leaving route/evidence assumptions stale.

## Locked work lanes

Lane minimum clear width is 2.4 world units, target visual width 2.6. They are packed/worn variations in the existing continuous terrain material, not floating planes or invisible path guides.

Required lane network:

- Central spine: north main gate -> camp center/furnace zone -> central river gate -> north-bank river lane.
- Cross-camp lane: west work gate -> storage/camp center -> east work gate.
- West shelter branch and east shelter branch from the cross-camp lane to the existing shelter sites.
- Continuous north-bank river lane from the west river-gate area through the central river-gate area to the east river-gate area, remaining dry and outside the wet/sloped bank.
- Short connectors from each of the other two river-facing gates to the river-bank lane.

The lanes do not add new stations, buildings, bridges, customers, machinery or Task 4 camera behavior.

## Gameplay collision and routing

- Player movement must collide with visible fence panels and slide along them rather than pass through.
- The six gate openings must be traversable in both directions at walk and sprint speeds.
- Collision uses the same segment authority as visuals; no invisible wall may exist where a gate is visibly open.
- Companions/population/threat records are kept off fence geometry by the same boundary authority. T26 remains responsible for complete population navigation under load.
- River collision/recovery remains authoritative and runs together with fence collision.
- Save restoration must never place the player/companions inside a fence panel; inventory, identities, jobs and progression remain unchanged.

## Historical progression

The two historical buildable barricade/defense records and all resource prices/unlock rules remain intact. T03 adds the static camp perimeter and gate network; it does not redesign T17 combat defenses or alter the 8 wood + 3 stone north-defense requirement.

## Required Task 3 evidence

The required order is **mechanical/regression -> cheap performance-budget preflight -> formal gate-specific visual preflight -> fresh C1/C2 -> C6 -> final pixel signoff**. Critics are not a substitute for obvious preflight checks.

Before Task 3 may pass:

1. Exact perimeter constants and all six gate definitions match this file.
2. South fence remains outside the T02 river permanent-build setback for every segment.
3. No fence panel obstructs the three reserved future river crossings.
4. Fence visual panels and collision segments derive from the same segment list.
5. Every gate is at least its locked clear width in collision; every river gate also passes the separate 3.20-unit visual-aperture gate.
6. Player walks and sprints through every gate in both directions.
7. Player cannot walk or sprint through representative solid fence sections, including corners and curved south-bank sections.
8. Continuous dry routes connect all required lanes without crossing water or fence collision.
9. All original functional suites plus T01/T02 acceptance suites pass.
10. T01 approved forest remains seated/unchanged and T02 river geometry, width, banks, recovery and crossing reserves remain valid.
11. A cheap pre-critic performance-budget check must reject obviously excessive draw calls or submitted primitives against the governed integration budgets. This is not physical-device FPS certification.
12. Each west/central/east river gate must provide machine-readable source-bound evidence IDs for exactly four required views: `river-side-approach`, `threshold-three-quarter`, `camp-side-outward`, and `gameplay-scale`. Missing or duplicate evidence blocks C1/C2.
13. With no explanatory caption, each river-gate evidence set must visibly communicate: protected camp -> authored gate structure -> clear threshold -> worn path through the threshold -> continuation toward the river lane. Captions may not rescue ambiguous pixels.
14. Source-bound actual renders also cover full perimeter, north/west/east work gates, south curved fence, central/cross lanes, both shelter branches, river lane, close panel/post contact, day/night/weather and native 3840x2160 scale-1 views.
15. Both separately executed critic roles must freshly review the repaired candidate and pass every applicable mandatory T03 dimension strictly >9.0 unrounded with no unresolved mandatory defect. A score of exactly 9.0 fails. Target remains 10/10.
16. Full C6 Performance Critic runs only after the visual critic gate passes. C6 mandatory dimensions also require strictly >9.0 unrounded and no unresolved defect.
17. Final pixel signoff checks the actual captures and raw critic observations rather than accepting scores blindly. Diagnostic confidence is recorded only as `low`, `medium`, or `high`; it is never expressed on the production 0–10 quality scale.
18. No unfinished APK or user benchmark is requested.

## Scope exclusions

T03 does not authorize Task 4 camera redesign, Task 5 station/prop replacement, bridges, paid pads, customers, fishing systems, new character rigs, later biomes or final device-performance claims. Necessary fence rendering, collision, terrain lane masking, route tests and evidence tooling are in scope.
