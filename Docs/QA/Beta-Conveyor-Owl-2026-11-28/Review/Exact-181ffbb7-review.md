# Havenline conveyor and owl playtest review

Independent reference review of `181ffbb7a1c22a4df9cda3af45cfbc9e7ebe9ef6` against gameplay evidence base `c9d5e3f9c588dbd2cff2a0def7744978be3f06a4`. Both requested scopes meet the 9.5 playtest bar on this candidate. The receipt binds the reviewed native files and frozen source hashes. The current progression exposes the expedition owl. [Evidence receipt](Exact-181ffbb7-review.json) · [Reference provenance](Authority.json)

| Conveyor criterion | Score |
|---|---:|
| Width and readability in fully paid camp | 9.7 |
| D01 material and fitting fidelity | 9.6 |
| Deck and cargo continuity and usable public space | 9.8 |

Actual 1×, 1.45× and 2× gameplay shows the wider belts as substantial equipment. The growing charcoal roller fields and taller orange edge faces stay visible behind transported resources. Cobalt ends, zinc bands and supports separate docks, turns and working deck. D01 studio fascia is brighter than the runtime specimen and A16's specialized dual-inlet food buffer still exceeds ordinary camp deck widths. Narrow turns and dock throats are less readable at 1×. The faint roof cutaway difference in one baseline warehouse pair is a timing-dependent view change, so use the matching cooker shot and exposed conveyor spans for that comparison. [Native final board](Exact-181ffbb7-belt-board.jpg) · [Before and after](Matched-transport-gameplay.jpg) · [Locked A16 inspection](A16-region-review.jpg)

The measured original deck was 0.484 m. There are 26 of 57 fitted sections at least 0.784 m wide. The widest utility section is 0.984 m, meal return 1.084 m, and serving branch 0.884 m. All eight typed routes were connected in the native fixture. The measured 53-check separate routes run exercises delivery, public aisles, deposits, and paid station relocation. Visible 1× and 2× frames confirm cargo on the deck and open space between stations. [Native frame data](../havenline-transport-owl/Belts-final/Transport.json) · [Measured route checks](../hl16belt/Transport-scale-and-routes.json)

| Owl criterion | Score |
|---|---:|
| Size and fixed-view legibility | 9.8 |
| Attack anticipation, contact and recovery | 9.7 |
| Planted perch and fence clearance | 9.8 |

The unchanged selected owl model and feather art are 30% larger on both flight and folded rigs. Folded rest height grows from 0.675 m to 0.8775 m, about half the nominal hero height. Flight wingspan grows from 1.0569 m to 1.3739 m. The folded claws remain on the post and the larger shape stands out against the snow cap. The blue scarf, pack and compact folded wings still merge at 1× on the rear-quarter perch camera, where bright nearby pad lettering competes with the silhouette. The original sheet shows perched views; the size ratio and airborne attack are gameplay choices with no locked counterpart in reviewed clips. [Perch comparison](Perch-matched-baseline-candidate.jpg) · [Selected owl](Owl.jpg)

At ordinary 1× the sequence shows takeoff, lateral bank, anticipation, descending strike, recovery and follow. Wing fold and talon contrast at that distance are subtler than the arc. The northeastern field case partly hides the high bank and anticipation under the upper HUD at 2×. Its in-frame strike shows the whole owl, a real single claw hit, damage marker and wolf flash, followed by an observable release. The alternate 2× field bearing adds a readable fuller windup and shows claws and body at contact, although the dive approaches the top HUD. The enemy health bar and damage numeral can still momentarily obscure feet or an outer wing. The two ordinary encounters show no pose break or collision masquerading as damage. [Ordinary 1× gate sequence](Exact-181ffbb7-gate-attack.jpg) · [Northeast sequence](Exact-181ffbb7-field-attack.jpg) · [Alternate field bearing](Exact-181ffbb7-low-bearing.jpg)

The measured gate wolf falls from 3 HP to 2 on one verified strike. The independent outdoor case identifies a different hit taking the boss from 8 to 7 during the dive, then exactly one owl contact taking 7 to 6. Damage remains one per hit. The attack allocates 0.30 s for the tell and 0.22 s for talon follow-through. Its reload is 2.30 s, down from 2.70. Final native-game checks pass 26 articulation and contact assertions and 11 live gate-patrol assertions. The previously reproduced fast-exit corner stall is absent on final field playback. Native motion traverses both gates in focused tests, returns to perch, and does not score through solid fence geometry. [Exact owl mesh/contact tests](../havenline-transport-owl/qa/final/qa_field_owl/run.log) · [Exact live patrol checks](../havenline-transport-owl/qa/final/qa_owl_gate_patrol/run.log) · [Native outdoor receipt](../havenline-transport-owl/Field-owl-final/Field-attack.json) · [Earlier corner reproduction](corner-geometry.log)

These are software playtest findings for the two changed scopes. The local native captures use llvmpipe. Fold7/device/memory/thermal coverage was outside this review. The inherited 200-wave stress fixture reports the same preservation failure on the beta baseline and candidate. No full release certification is inferred.
