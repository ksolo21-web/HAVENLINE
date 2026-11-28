# Havenline Beta T03 gates and work lanes

T03 carries the reviewed T02 world into the current two-gate camp. The two working entrances are the south gate and east gate, both earned when the player founds camp. The old six-opening river-facing prototype remains historical evidence for later layouts.

The fence retains substantial golden timber, round lash rails and scalloped snow crowns. Ropes stay readable at gameplay scale, and the gate tops follow the rounded snow profile in the owner sheets. Each visible leaf swings from its hinge and shows its framed rear or X-braced exterior according to viewing side. The solid wall collider is 0.60 m deep and uses the same wall segments as the fence art. The widened depth covers the rounded stocks and rails while preserving the gate opening.

The forester chooses a feasible entrance for a field route based on route length. When arriving opposite the player, the forester can step to the side and resume once the player clears the entrance. The movement constraint keeps actors apart inside the approach. The four loaded head-on traffic tests kept feet over 0.74 m apart while both actors completed their crossing.

The reference review used the six GitHub owner sheets, frames from B at 6, 8 and 10 seconds, and the available B gate motion excerpt. Provenance for the later B 18–22 second window was found. The original pixels for that window were unavailable in the checked sources.

## Captured evidence

Native Godot Compatibility renders include both gates from inside and outside, actual 2× pinch, coded open and closed states, a fence corner and the 3840 × 2160 court at render scale 1.0. The loaded touch replay shows the south inbound crossing at 1× and the east outbound crossing at 2×. All resulting route samples remain seated at y 0.

The representative software 4K court submitted 532 draw calls and 949,566 primitives, within the project's 650 draw and two million triangle preflight budgets. The current 460 × 760 court capture submitted 395 draw calls and 567,202 primitives. The prior T02 capture submitted 374 calls and 547,932 primitives. These are single-frame submission observations. Physical device and sustained workload testing were skipped for this playtest.

[Playable source](Candidate.json) · [Owner sheets](Reference/Owner-selected-six-sheets.jpg) · [Side-by-side views](Review/Exact-save-final-board.jpg) · [Native 4K court](Capture/Court-4K.jpg) · [Loaded touch replay](Capture/Loaded-two-gates.mp4)

## Verified behavior

All 16 focused suites passed. The route matrix exercised 168 touch approaches from each starting load condition across three expansion stages. Separate independent checks completed all 16 mixed-cargo player passes, eight touch collisions against the solid timber, and four full automatic gate cycles with both directions tested. Each loaded worker route preserved its cargo ledger. Live wolves pursued and bit the player outside each gate while respecting the fenced sanctuary.

The exact-source independent review awarded 10/10 for each C1 reference and C2 geometry dimension. The gate's mechanical opening motion also scored 10/10. The retained replay shows loaded traversal at ordinary and pinch zoom, and the cycle log proves that both gates re-latch after the approach clears.

Older saves made alongside the thinner fence now use the current wall depth to find standing room. Eight saved positions across both faces of the four fence runs tested safe recovery on the original side with HP retained. Independent cold reopen tests also verified paid camp state and cargo on both sides.

[Final independent review](Review/Exact-7bc640e9-review.md) · [All suite exit codes](Tests/Suites.txt)
