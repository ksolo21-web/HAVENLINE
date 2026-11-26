# Havenline Level 1 field review

Alfred can watch the playable opening from an empty pack through mining, hunting, construction, storage and the three-tool upgrade. The footage follows Character 1 through both gates in both directions. [Full gameplay movie](Field-Loop.mp4) · [Capture settings and results](Gameplay-QA.md) · [Native 4K frames](Gameplay-Stills/)

**Runtime commit** `994ace861fbf132c5924bacc320f5608d75d9187`  
**Godot scene** `res://field_opening.tscn` in `HavenlineLevel1/project.godot`  
**Engine** Godot 4.7.2. [Browse the exact source](https://github.com/ksolo21-web/HAVENLINE/tree/994ace861fbf132c5924bacc320f5608d75d9187/HavenlineLevel1) · [Controls and reproducible test route](https://github.com/ksolo21-web/HAVENLINE/blob/994ace861fbf132c5924bacc320f5608d75d9187/HavenlineLevel1/docs/Field-Loop.md)

[Prepare the exact playable project and export templates from GitHub](Build/) · [Packaged builds and checksums](Package-verification.json)

## What passed in this opening

| Area | Earned result |
|---|---|
| Resource and tool scale | Character 1 occupies roughly 12% of the short screen dimension at normal zoom. The starter orbit takes about 0.89 s and expands from one tool to three on payment. The mining approach leaves the pick head and the struck rock visible against the snow. [Reference comparison](References/Independent-field-review.md) · [Quarry camera evidence](Environment-QA/Quarry/) |
| Harvest, hunt and carry | Axe hits fell a pine, pick hits deplete the rock and a defeated wolf drops meat. The return to camp shows three wood, three stones and two steaks on separate parts of the pack. [Turnaround and mesh fingerprints](Gameplay-Evidence/Field-art-provenance.json) · [Wood end grain](Gameplay-Evidence/Wood-end-grain.jpg) |
| Payment, storage and upgrade | Three wood construct the central furnace and fenced court. The route stocked six wood, three stone and two meat before spending two stone and one meat on the orbit. At the recorded quantities, each stored unit is visible, and an emptied plot regains its material marking. [Economy checks](Economy-QA/) |
| Gates and snow | The physics clock recorded south outward 27.61 s · south inward 33.82 s · east outward 48.63 s · east inward 51.81 s. Snow remains outside the paid court. The normal and 2× camera use the same angle. [Court checks](Environment-QA/Field-court.json) |
| Locomotion | Independent score **9.1/10**. Four thousand tested poses cleared the opposite boot and shin. The last swing in a hard turn is still wide and brisk. [Rig score, hashes, gait evidence and verifier details](Character/Independent-QA/V12-16b75a22/Review.md) · [Normal and pinch motion](Character/V12-Character-Movement.mp4) |
| Audio | The 53 WAV files reproduce from five fingerprinted Havenline originals and the included generator. The main route triggered 39 of the 41 named cue types. The separate injury route covers player fall and recovery. The final waveform check identifies purchases, reveal and victory among 110 individual matches. Some quieter overlapping activations could not be separated in the mix. Music and ambience respond to the snowfield, wolf encounter and earned hearth. [Full-film audio review](Audio-QA/Independent-audio-review.md) · [Cue bank and injury route](Audio-QA/Independent-expanded-audio-review.md) |

**Field loop passes at 9/10.** The field-camera critic reviewed the complete 53.233-second, eight-chapter movie at the ordinary gameplay camera, the moving pinch, the two native 4K routes and both corrected problem areas. The second review also scored spending and construction legibility at 9/10. The differences most visible against B are its stronger ignition and upgrade flashes, Havenline’s darker wolves and the broader axe head. [Full field verdict](References/Second-field-review.md) · [Reference B beside this opening](References/Reference-vs-final-game.jpg) · [Ignition and floor reveal, frame by frame](References/Reference-vs-earned-hearth.jpg)

## What still needs production verification

The applicable field and motion verdicts cover this one playable opening. The complete production reference lock still requires the broader rescue, companion harvesting, cooker and customer flows, later defense and multi-character coverage. Seven historical task approvals have open visual invalidations. The full T01–T11 audit identifies the source and remaining evidence for each. [T01–T11 audit](T01-T11-review.md)

Native 3840×2160 and 2160×3840 images exist at normal and 2× pinch. The review machine renders through Mesa llvmpipe. During a concurrent 720p recording, median 4K frame intervals across the four software-rendered views ranged from 7.53 to 15.23 seconds. A physical phone or tablet was unavailable for a sustained 4K 60/120 FPS measurement. [Available-device timings](Environment-QA/Available-device-performance.md) · [Export verification](Package-verification.json)

The first recipe uses the existing Havenline layout. The two-stone, one-meat upgrade and 2× zoom cap are branch tuning choices. The darker wolf follows Havenline’s art. Meshy usage was 15 credits for this wolf, taking the observed balance from 7,465 to 7,450. Every gameplay recording used a disposable test profile. [Visual and Meshy source records](Gameplay-Evidence/Field-art-provenance.json)

## Reference footage

The design and rigging notes connect the camera measurements, gesture controls, planted feet, resource details and touch-device frame budgets to their sources and tests. [Research and production decisions](Production-research.md)

The locked A/B excerpts retain their source timestamps and extraction receipts. Additional publisher and independently uploaded Whiteout Survival videos are catalogued with links, provenance and observed similarities. The full soundtrack for reference B was unavailable for musical comparison. [Original reference excerpts](References/Locked-sequences/) · [Additional videos and ads](References/Supplemental-videos.md)
