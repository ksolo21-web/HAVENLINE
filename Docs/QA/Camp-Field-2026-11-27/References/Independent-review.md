# Independent Level 1 playtest review

Game source `2654f5019b7212968d28600cb071bf1c231c9030`. Signed Android package SHA-256 `af81181c81bc623310b00680ea4467615c6f9ffd4c21c1197bc75aff3b71bd75`. These scores cover the named gameplay checkpoints. The current release policy requires separate per-dimension final reference reviews. [Forward acceptance standard](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/REFERENCE_ACCEPTANCE_STANDARD.md)

| Scope | Independent score | What the recorded run showed |
| --- | ---: | --- |
| Field pickup and retention | 9.5/10 | The keeper collected 72 scattered meat and stone bundles with typed balances, across a saved and reopened camp. A second crowded fixture kept all 128 uncollected receipts. |
| Warehouse approach and transfer | 9.5/10 | An ordinary load sent each parcel. At 52,000 displayed units, 12 visible packets landed in four durable groups at 0.28, 0.48, 0.68 and 0.88 seconds. The starter loading apron accepts deliveries while its upgrade requires a deliberate stop on the adjacent pad. |
| Cooked meals, receipts and stored money | 9.5/10 | Three cooked meals went to the counter and four previously earned notes entered the pack during a single 0.82-second approach. Seven deposited notes occupied and then cleared the warehouse cash shelf. Connected machines process and discharge unattended. |
| Worker carrying and service | 9.5/10 | One paid worker approached the loading door carrying distinct stacks of 120 wood and 120 stone. Both filed into the shelf in 0.85 seconds. The relocated cooker and customer station stayed serviceable in the actual AI job sequence. |
| Paid owl field and gate defense | 9.5/10 | The owner’s owl left the gate perch, visibly struck a real exterior enemy while the keeper was safe, then engaged a boss near the injured keeper. The paid and returning camp states passed separate checks. |
| Solid fence counter | 9.5/10 | All 60 original approaches, heights, side and saved-placement cases held the wall. The inside helper and outdoor customer remain on the intended sides in both normal and pinch views. |
| Tower, operator and approach | 9.5/10 | At both camera scales the gunner stands behind the bow on a timber tread. Two gloves engage their controls in 397 consecutive poses and 18 elevation extrema. The cabin stays opaque when the keeper passes behind. A released bolt reduces the exterior wolf’s HP from three to two. |
| In-world withdrawal from storage shelves | 9.9/10 | The game camera stays live at normal and 1.7× zoom as the keeper walks to the cash shelf. Seven earned notes fly into the pack, leave the door with the keeper, and redeposit on a later return. The same shelf approach worked for all ten raw materials, finished goods and cash types. |
| Large mixed pack at normal and pinch zoom | 9.9/10 | The 52,000-unit mixed load stays near the keeper’s shoulders. The keeper, door and objective remain visible at 1× and 2×. A small six-material pack remains clear of the upper controls with the threat notice active. |

## Character movement

| Rig | Native skin joints | Gameplay score |
| --- | ---: | ---: |
| C1 | 64 | 9.9/10 |
| C2 | 64 | 9.9/10 |
| C3 | 64 | 9.9/10 |
| C4 | 64 | 9.9/10 |
| Forester | 18 | 9.9/10 |

The game picker selects four distinct compact explorers. Character 1 supplies Idle, Walk, Run and FieldRun to the field controller. Each alternate has its own 64-joint skin and material, and follows the shared gait with body-specific fitted joints and boot contacts. Character 2 has the bob and glasses, Character 3 the open cream waistcoat and loose curls, and Character 4 the headband and laced boots. The forester runs and works on a separate 18-joint rig. [Owner and actual game models](Owner-identity/Approved-characters-in-game.jpg) · [Model identities](Owner-identity/Identity-correction.json) · [Original clip inspection](Rigs/Character1-original-clips/part-surface-and-joints.json)

Character 1 drove the normal touch scene for 545 consecutive samples at 120 Hz, empty and carrying a mixed pack. The 0.417-second full stride corresponds to about 4.8 steps per second. Projected travel was 4.67–4.72 body heights per second. The owner’s B gate shot spans roughly 0.40–0.47 seconds per full stride. The separate free-running shot has a slower passage. Both were reviewed frame by frame at the source frame rate. [Gate sequence](Original-gate-run-every-frame.jpg) · [Free-running feet](Run-support-and-lift.jpg) · [Real source and field comparison](../Motion/C1-source-and-field-run.mp4)

Left and right knees stayed forward during the control sequence. The same planted patch of leather moved at most 3.37 mm for Character 1 during the ordinary supported straight pass. Forefoot hinges bend through toe-off. The fitted cuff, boot fasteners, sleeves, hips, wrists and texture surfaces were inspected at multiple angles. A 90-second AI shift showed the forester traveling, bringing stock home, turning in place, collecting and serving. Among 1,961 recorded skinned poses the boots had zero opposite-side material intersections. Worst supported travel drift measured 0.65 mm. The longest planted-turn displacement measured 6.69 mm. [Rig gates](Rigs/Rig-release-gates.json) · [Part-by-part ledger](Rigs/Rig-inspection-ledger.json) · [Worker positions and load](Rigs/Forester-natural-work.json) · [Opposing shoe surfaces](Rigs/Forester-opposing-boots.json)

Characters 2–4 each ran the 545-tick route twice, empty and carrying. Their two-step cycle measured 0.417 seconds. Maximum drift of a planted boot patch was 2.95 mm for Character 2, 2.26 mm for Character 3 and 4.28 mm for Character 4. Complete hand and garment surfaces showed no new exposed glove crossings across the 3,270 poses. The final transitions lifted the recovering toe clear as the actor launched, steered and stopped. The duplicate seven-angle reviews expose the boot, cuff, leg, hip, shoulder and glove surfaces. Normal and 2× field recordings show the same bodies running under the ordinary controller. [Game footage and rig provenance](../Motion/Corrected-players/Release-gameplay-recordings.json) · [Final joint and contact ledger](Rigs/Rig-inspection-ledger.json) · [Previous worker turn defect](Iteration2/Forester-pivot-defect.jpg)

## Scope and constraints

The three corrected model portraits use common white lights and linear tone mapping. The underlying concept lighting is unavailable. The tested neutral cheek samples remain 6.8 L* lighter for Character 2 and 8.5 and 5.0 L* darker for Characters 3 and 4. Their gloves also read darker in neutral light. The gameplay crops retain the field camera’s own lighting. [Neutral color comparison](Owner-identity/Neutral-material-swatches.jpg) · [Sample method and coordinates](Owner-identity/Neutral-material-swatches.json)

The gameplay and pinch captures use Godot’s actual field renderer. The 120 Hz measurements describe physics and skin evaluation. A physical Galaxy Z Fold 7 run and a sustained 4K Ultra GPU frame-time measurement remain open. The revised 52,000-unit mixed pack preserves the keeper silhouette at normal and pinch zoom in the final signed source. [Field stress test](../Field/Field-and-storehouse.md)

This review gives the game behavior, clip and model evidence for the scopes in the table. Asset turnarounds identify the designed silhouettes. Timing, item landing and work motion come from the original gameplay videos. The defense structure itself is identified by the owner’s dedicated ballista sheet. [Reference identities and source hashes](Sources.json) · [Original chosen models](Owner-approved-designs.jpg) · [Package evidence and scored films](Verdict.json)
