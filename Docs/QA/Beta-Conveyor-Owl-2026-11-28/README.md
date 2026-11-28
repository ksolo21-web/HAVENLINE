# Havenline beta conveyor and owl playtest

This patch follows the published T05 station-kit source. [Frozen source and fingerprints](Candidate.json) · [Independent gameplay review](Review/Independent.md)

## Conveyors

Paid conveyor spans use wider orange-framed decks where there is room, drawn from the selected Havenline transport kit. The modules taper at the existing machine sockets, turns, and reserved walking approaches. The customer counter has a 1.084 m receiving deck, up from 0.484 m, at the right end of its default site. Fresh and stored meals can reach it automatically and feed separate physical stock slots. The forester can cross the workshop floor and reach the saw along the preserved west aisle.

The native captures use the same player camera at 1×, 1.45× and 2× in an isolated paid save. No art generation credit was needed for this pass. [Before](Conveyors/Before/Transport.json) · [After](Conveyors/After/Transport.json) · [Installed fits and live route tests](Validation/Transport-scale-and-routes.json) · [Receiving and sale stages](Conveyors/Live-stock/Stock.json)

## Expedition owl

The playable owl is 30% larger in both the perched and flying models. The pronounced bank and anticipation make the dive legible. One swept talon contact deals one damage and can interrupt a wolf that is preparing to bite. The claw stays on the animated target through the brake, then releases into recovery. The repeat gate strikes are 3.283 seconds apart in the patched run, down from 3.600. The health bar and concurrent damage labels move beside the target briefly during contact and release.

The fast-exit scenario confirms a bank, windup, dive, single contact, and recovery after the owner travels through the gate. The earlier corner-stall reproduction is retained. [Baseline native playback](Owl/Before/Owl-gate-intercept.mp4) · [Patched native playback](Owl/After/Owl-gate-intercept.mp4) · [Field contact at pinch zoom](Owl/Field/Strike-2x.jpg) · [Patrol measurements](Owl/After/Patrol.json)

## Verification scope

The review rates conveyor cargo continuity and owl attack at 9.9/10. Belt scale, belt fittings, owl scale and perched readability are 9.8/10. These results qualify for the playtest checkpoint and leave the 9.9 final reference-sensitive pass open. [Independent review](Review/Independent.md)

The selected videos and renders set the conveyor and owl appearance reference. The selected owl sheet depicts perched poses. Its relative scale and flight attack are authored gameplay choices. The native renderer was Godot Compatibility using llvmpipe at 960×540. Device and sustained performance have no new evidence here. The separate inherited 200-wave stress fixture reports the same actor-preservation failure on exact T05 and on the initial patched candidate. [Reference sources](References/Authority.json) · [Encounter baseline](Validation/Encounter-baseline.log)
