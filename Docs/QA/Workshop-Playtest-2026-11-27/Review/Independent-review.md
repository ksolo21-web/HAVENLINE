# Havenline Build 15 independent playtest review

## Reported progression blocker

I reproduced the garage behavior in untouched Build 14 `b92588e389f429776a11e7d0349d2096311000ca`. I opened the archived cooker-only profile through the ordinary native save path and staged the reported carried totals through the normal resource ledger. The profile started with a paid cooker, an offered saw bench, and a locked quarry drill. I used synthetic mobile touch to walk through the south gate and stand next to the offered garage.

| At the garage in Build 14 | Measured |
| --- | --- |
| Carried | 1,460 wood, 130 stone, 360 meat |
| Planks and blocks in pack or storage | Zero |
| Garage due before and after 155 physics ticks | 24 planks and 20 blocks |
| Truck purchase | Locked |
| Next workshops | Saw bench offered at 140 wood and 60 stone. Quarry drill locked until the saw bench is bought. |

Raw goods did not advance the garage receipt. The state can be resolved eventually by building and operating both workshops, but the optional garage plot advertised a price before this camp could produce its inputs. [Build 14 route evidence](Build14-garage-blocker.json)

## Raw garage retest

The same profile and reported raw totals passed 9/9 checks in the updated Build 15 field. The normal touch route paid exactly 180 wood and 120 stone from the pack, with no planks or blocks in the pack or warehouse. The garage appeared and the truck plot opened while the saw and quarry drill remained unpaid. The carry counts went from 1,460 to 1,280 wood and from 130 to 10 stone. Warehouse raw stock remained unchanged. [Build 15 route evidence](Build15-raw-garage.json)

## Manual workshop acceptance

A paid, working cooker, saw bench or quarry drill should be operable by the player from its adjacent public apron with no survivor or conveyor installed. The station details should point a distant player to a reachable input or output. Within reach, the player should be able to load matching raw goods from the pack, let a real cycle finish, and collect its typed product exactly once. An empty neighboring plot should leave workshop access available. An owned conveyor may continue operating during manual player handoff. The handoff mode is a session preference for this playtest.

Three independent native touch routes passed. The cooker passed **20/20** in an actual rendered 460 × 760 scene. The quarry drill passed **20/20** and the saw bench passed **21/21** in headless native scenes. Each route opened Camp → Workshops, selected a paid machine, chose manual handoff, followed its input guidance and used the visible load and collect buttons. Each produced three new units. The cooker also retained one prior output from the archival fixture, so its collected quantity was four. All other collected quantities were three. Duplicate collection checks passed. [Cooker screens](Cooker-mobile-controls.jpg) · [Cooker data](Cooker-touch.json) · [Drill data](Quarry-drill-touch.json) · [Saw data](Saw-bench-touch.json)

At a 60 Hz simulation rate, the manual input began with a valid action press. The first matching lot reached the hopper seven ticks later and the last of the three lots left the pack after eleven ticks in each route. Production then completed each machine’s own cycle. The two processor guidance points were inside the interaction radius, with roughly 9–10 cm of nominal margin. [Cooker phase evidence](Cooker-touch.json)

Furnace, fuel and metal production are design work for a later test.

## Locked reference and current tower diagnosis

Original recording B is `Screen_Recording_20260817_124510_YouTube.mp4`, SHA-256 `4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2`. Saved original-source evidence contains the B42.40 payment, B43.00 installed defense, B43.70 hit and B44–52 later defense views. The open ballista and defense-platform sheets are pinned at `2ae9702b0b6294b6cca3fa0d3098025d72484f06`. The alternate roofed watchtower is pinned at `b80c61f13ba31bb0940792dd47976a8e2878dbf5`. [Recording manifest](https://github.com/ksolo21-web/HAVENLINE/blob/b80c61f13ba31bb0940792dd47976a8e2878dbf5/Docs/Design/ReferenceVideoLock/reference-video-sources.json) · [Original frames and owner tower sheets](Tower-references-and-Build14-baseline.jpg)

The Build 14 return route reproduced the visual complaint at 2×. A large ghosted player torso and boots projected across the deck, guard and launcher. The stone base still had opaque surfaces. The overlapping actor projection made the defense look transparent and muddled which character operated the launcher. Review the replacement from the same approach at normal zoom and 2× with a distinct guard, readable launcher, and clear player location.

The revised tower scored **9.5/10** for the reported presentation repair. Matched actual-field views from the stone-return route now keep the base, deck and ballista opaque. A compact cyan locator indicates the player where the structure blocks sight. The clear-side and turning views separate the guard and player, and the release frame shows the distinct working launcher. The hero’s visible head can still line up behind the guard on one 2× sightline. [Paired normal and 2× evidence](Tower-candidate-board.jpg)

The worker source is the selected male survivor turnaround at `01664a73ddf5087f17f7e159fa0b6b4ed71367b5`, SHA-256 `03a84c4c781047b66f6c9f197f687010b4de52087f53027328cf8a45570cd27e`. Original B at 6 seconds supplies actual harvesting context. The selected survivor sheet establishes body, clothing and equipment appearance. A precise repeated survivor chopping or mining beat is not established by that frame. [Selected survivor turnaround](https://github.com/ksolo21-web/HAVENLINE/blob/01664a73ddf5087f17f7e159fa0b6b4ed71367b5/Docs/Design/RenderArchive/2026-11-23/selected/characters-survivors-npcs/survivor_male_01.png)

## Worker motion review

The first Build 15 worker repair completed autonomous repeat chopping, mining and returning goods. The independent pose check uses the exact imported 18-joint survivor, supplied tool meshes and procedural Chop/Mine playback. The model has no embedded animation clip. The action cycles are 1.55 seconds each. I rendered nine complete-body poses from six directions per action in Godot Compatibility and scanned 187 samples per action at 120 Hz. The planted soles stayed within one micrometre of their starting locations in this isolated stance and the palm centers stayed on the modeled grips.

The first pose candidate remains below the visual gate. Both actions contained palm rotations around 93 degrees in a single 8.33 ms interval. Mining also produced a left forearm step of 68.6 degrees and an upper-arm step of about 39 degrees around phase 0.44. The right, left and rear views show the raised mining tool overlapping the head and collar during part of its return. [Initial chopping poses](Forester-chop-initial-six-angles.jpg) · [Initial mining poses](Forester-mine-initial-six-angles.jpg) · [Angular evidence](Forester-initial-angular-witness.json)

The original forester axe was a different asset from the owner-approved game axe. The current implementation points to the gameplay `axe-field-grip.glb` and `pickaxe-meshy.glb` from `weapon_orbit.gd`. Both files match the approved hashes. The first fixed-tool candidate still placed the physical handle against the worker’s face or collar. A separate test skinned the actual imported character at 120 Hz and tested tool edges against head and collar triangles in both directions. The reconstructed bind pose agreed with the imported mesh within 2 nanometres. The revised mining path reduced crossings from 131 to 60 head samples and removed the visible arm-solver snap. The sampled weapon clearance gate remained open on that revision. [Approved tools](Approved-tool-provenance.json) · [Upper-body clearance retest](Forester-approved-v3-clearance-rejected.json) · [Exact rig timing](Forester-approved-v3-angular-witness.json)


### Exact Build 15 result

The release snapshot `4de1b9edb0230c8c33b8d872ded47ef914a0f87f` has the same solver hash as the tested revision, `1bcc70dc2a3787dbd474bc58d05ad0eaef3cdc582f6961e275c6d04b2b5e3d63`. Native field runs passed 8/8 in both rendered and headless sessions. The worker struck three distinct trees nine times and landed six pick hits across two depletion cycles of the starter stone bank. Six timber and four stone delivery receipts reached storage with the player parked. First verified wood and stone hits were at 3.6 and 45.3 seconds in this fixture. The game uses approved meshes and their physical edge and tip. The audit camera was centered on the worker for capture while the player stayed parked. [Field replay and exact contact events](../Crew/Harvest-replay.json)

The independent axe sweep and the exact paired solver sweep both found zero sampled surface crossings with the head or collar across all 187 phases per tool. Studio playback uses the imported 18-joint survivor and the same action code. I checked both actions through nine full-body phases at six angles, alongside captured field views at 1× and 2×. At 120 Hz, the largest single bone step was 8.58° for the axe and 3.39° for the pick. The largest start-to-end bone difference was 0.04°. Measured sole anchor drift and palm-center error were each below a micrometre. This 18-joint asset has fixed mitt geometry and no independent finger joints. [Axe poses](Forester-approved-chop-six-angles.jpg) · [Pick poses](Forester-approved-mine-six-angles.jpg) · [Actual field views](Forester-approved-field-contact.jpg) · [1.55-second loop measurements](Forester-approved-v8-angular-witness.json) · [Independent clearance](Forester-approved-v8-independent-axe-clearance.json) · [Paired exact clearance](../Crew/Forester-tool-clearance.json) · [Source checksums](Forester-approved-v8-source.sha256)

| Scoped presentation | Score | Remaining visual issue |
| --- | --- | --- |
| Repeated survivor chopping at gameplay zoom | **9.0/10** | The compact chest-level swing gives the axe little visible separation between preparation and contact. Trunk chips carry much of the impact at 1×. |
| Repeated survivor mining at gameplay zoom | **9.3/10** | The raised pick and body load read more clearly. Its head still overlaps the survivor's face in projection during recovery on the tested approach. Physical head and collar clearance passed. |

Across the eleven sampled field phases, the axe edge traveled 30.1 cm between its farthest positions and changed height by 10.3 cm. The pick tip traveled 45.9 cm and changed height by 38.9 cm. These measurements use the physical tool tips in the worker’s coordinate frame. [Field motion samples](../Crew/Harvest-replay.json)

The approved-tool identity, repeat work, planted stance, grip, physical contact, and tested head and collar clearance passed. The visible chopping and mining motions remain below the 9.5/10 quality bar. [Live 2× chop sequence](Forester-approved-chop-sequence-2x.jpg) · [Live 2× mine sequence](Forester-approved-mine-sequence-2x.jpg)


### Isolated motion refinement

The later refinement `b178831d59d917413624b9e8e6ad99ca677cc4761ce82ec38316d528d87c9973` was reviewed in a separate checkout. The native route again passed 8/8 and the bilateral geometry check found zero tool crossings with the head or collar over 187 samples per tool. The dense test shows planted soles, secure grip and a largest single bone step of 11.0° for chopping and 3.39° for mining. [Route and tip measurements](Forester-polish/Field-comparison.json) · [Clearance](Forester-polish/Tool-clearance.json) · [Angular witness](Forester-polish/Angular-witness.json) · [Source checksums](Forester-polish/Source.sha256)

I scored chopping **9.2/10** on this refinement. The windup is easier to distinguish at 2× when the axe opens to the right. Its edge traveled 41.3 cm compared with 30.1 cm before. Most of the added travel is sideways, with vertical movement increasing by only 0.8 cm. At 1×, the stroke still reads mainly as a short forward cut with limited shoulder load. I scored mining **9.3/10**. The pick arc remains distinct, and the revised recovery looks nearly identical from the tested gameplay angle. The refinement falls short of 9.5 in both motions. [Chop at 1×](Forester-polish/Chop-1x.jpg) · [Chop at 2×](Forester-polish/Chop-2x.jpg) · [Mine at 1×](Forester-polish/Mine-1x.jpg) · [Mine at 2×](Forester-polish/Mine-2x.jpg)
