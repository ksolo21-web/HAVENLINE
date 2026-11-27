# Character 1 and survivor locomotion

This review uses the running game, the actual source models and two moving subjects from original Whiteout Survival footage. The camera is Havenline's gameplay camera. Native-input tests used a temporary, sentinel-locked profile.

[Watch both Havenline characters beside their reference footage at real speed and one-third speed](Player-and-worker-motion-comparison.mp4)

## What changed on screen

The compact Character 1 passes the revised running review at **9.5/10**. Previously the knee folded to around 65° almost immediately after the foot landed. That made the body appear to squat, then snap upright. The revised run takes weight on a bending knee, extends the rear leg through toe-off, folds the shin in flight and opens it before the next strike. Tracking the whole left knee curve against the human comparison reduced root-mean-square deviation from 30.3° to 6.6°. The test uses an adult runner at 4.5 m/s as a biomechanics check for the stylized character. The measured top game speed of 6.25 m/s was preserved.

- [Compact player at gameplay zoom](Compact-V7-1x-gameplay.mp4)
- [Compact player at pinched zoom](Compact-V7-2x-gameplay.mp4)
- [Build 8, both characters at 60 frames per second](Build-8-player-and-worker-60fps.mp4)
- [Full-stride knee timing for both characters](Knee-timing-player-and-survivor.png)
- [Six-view player surface check](Compact-V7-six-views.jpg)

I measured 545 live poses at 120 Hz while ordinary touch input accelerated, turned and stopped the player. The corrected run keeps its fleece cuffs intact through all four clips. The same individual patch of sole moves 19–32 mm during the five measured support intervals. There is still a small amount of tread slip and the long coat partly hides the knee at default zoom. [Material-point observations](Compact-V7-planted-material.json) · [Source hashes](Compact-V7-source-sha256.txt)

## Survivor

The frozen survivor passes the revised gameplay locomotion review at **9.5/10**. I recorded his actual first wood delivery, starting immediately after he picked up the logs. All 65 consecutive frames of the 60 fps clip are distinct. The player stands still as the loaded survivor rounds the tree and approaches the open south gate. Both characters overlap briefly at the gate. I also checked the worker builder’s 42 distinct close-camera frames. The timber stays on his back while his boots continue through the open leaves and onto the camp floor. [Pinched gate passage](Forester-gate-pinch.jpg) [Play the delivery at real speed and one-third speed](Forester-carry-60fps.mp4) · [Inspect consecutive frames](Forester-carry-consecutive-frames.jpg) · [Verify capture and gameplay state](Forester-field-camera.json)

The original forester traveled at 1.8 m/s using a walk. The rescued forester now accelerates into a run and shortens his steps as he takes a corner. The ordinary paid-rescue and first loaded delivery produced 6.25 m/s of straight-line travel on the frozen candidate. An intermediate revision showed a knee angle fixed at 17.46° through 17% of a stride. The final curve has four distinct extrema, mirrored across the two legs.

| Phase | Share of same-foot stride | Knee bend |
|---|---:|---:|
| Weight acceptance | 15% | 43.5° |
| Extension after push-off | 32.5% | 14° |
| Peak swing recovery | 65% | 119° |
| Reach before strike | 97% | 15° |

I tested 1,351 actual boot vertices at 241 consecutive poses. A recovering boot previously slid 12.5 cm while hovering 3–4 mm above the ground. The same part of the boot now clears the snow by 50–57 mm. Fitting the ankle to the roll of the tread reduced the maximum sustained near-ground slide from 63–68 mm to 4.5 mm on each side. [Imported model in six views](Forester-six-view-rig.jpg) · [Full curve](Forester-241-sample-curve.json) · [Independent sole measurements](Forester-independent-sole.json) · [Frozen inputs](Forester-frozen-source.txt)

## What the reference actually shows

- **Hero, 6–10 seconds.** In the first second he waits on a purchase then pivots. From 7–8 seconds the near boot trails the coat and swings back under it. He briefly pauses on the next mat. From 8–9 seconds he turns again and sets off. At 9–10 seconds he enters the water. Every source frame is preserved at 30 fps, followed by one-third-speed playback. [Play source](Reference-player-real-then-third-speed.mp4) · [Read consecutive frames](Reference-player-every-frame.jpg)
- **Hero, 32.6–37.8 seconds.** He runs toward the timber at 32–33 seconds, advances between the stacks at 33–34, bends around the lumber at 34–35 and 35–36, and emerges into the aisle at 36–37. The lumber intermittently hides the far boot. Each of the 157 decoded frames is retained, including turns and occlusions. [Play field run](Reference-player-field-real-then-third-speed.mp4)
- **Separate delivery worker, 27.5–30.83 seconds.** The blue-coated player stands at the counter while a cyan-clad worker approaches with fish, unloads, runs back for another fish and returns. The first delivery spans 27–28 seconds, the unloaded return starts at 28.75 seconds, the next pickup is visible around 29.25 seconds and the second delivery reaches the counter around 30 seconds. The hat and boots distinguish him from the player throughout. His screen travel measures about 6.0 projected body heights/s before braking, and 4.9 including the brake. All 81 consecutive original frames run at 24 fps. [Play worker trip](Reference-worker-real-then-third-speed.mp4) · [Inspect stride](Reference-worker-every-frame.jpg)

The owner-locked A/B excerpts are available at their recorded sample interval of 100 ms. They show an approximate 3.2 body heights/s in A's opening carry and 5.0 in B’s faster upgrade approach. The adjacent 30/24 fps original ads show motion between those coarse samples. Neither the heavy coats nor this camera angle exposes exact source joint angles or a continuous view of both soles. The release rating reflects gameplay and the recorded physical tests. [Source ledger](Observed-source-frames.json) · [Primary-source measurements](Locked-reference-screen-speed.json) · [Human running dataset](https://doi.org/10.7717/peerj.3298)

## Taller Character 1 A

The taller prototype scores **9.0/10** for its gameplay run. The same-height comparison uses the original Winter Welcome articulated model at the same world height of 1.75 m. Its longer leg silhouette makes the knee and boot swing easier to see. The V7 prototype maps 50 joints and measures an 18.3 cm peak clearance for both boots during steady travel. Both soles clear up to 5.7 cm at once. I measured 29–50 mm of movement in the longest-observed support patches. At 1.4–1.73 seconds in the fifty-joint version, the rear view exposes the wide lifted arms and splayed fingers. At pinched zoom the lifted glove briefly projects beside the glasses, and the rear turn makes the wide arm carriage visible. [Fifty-joint trial at pinched zoom](Taller-A-V7-2x-gameplay.mp4) The compact player retains a more relaxed silhouette. [Fifty-joint trial at gameplay scale](Taller-A-V7-1x-gameplay.mp4) · [Browse rear and side poses](Taller-A-V7-1x-camera-sheet.jpg) The source model has 727,442 triangles and six hand-test clips. The current compact gameplay model has 25,333 triangles and its own authored locomotion clips. Performance on a physical Fold 7 has not been measured for this comparison. [Actual native tall trial](Taller-A-native-physical-trial.json) · [First tall comparison at pinch zoom](Taller-A-V3-prototype-2x-gameplay.mp4)

## Source binding

Both active and clean-export files matched the frozen Level 1 source commit `17abe3795bb91e6a80b48d93bab7578ad2ad4aed`. [Verified scene and file digests](Final-source.json)

The compact player uses GLB SHA-256 `e165a24b6b1205904165e0f1aad643c2fc2e00152df5d58de218e7ca7e375eff`. The rescue worker uses GLB `8768255badde45f66114c5fefbada73771873558ce117b8360bf4cea96acc88c` and forester gait `64a1bd6aab7719259f2472803502ea70bbdccc98f5afc950498cedc29cc0c4b2`. Tall A uses GLB `2fabd0fd357cc18f98142cfad47fd118421dde772cc50b24d1d481f5ca9fcb2e`. All gameplay observations refer to `res://field_opening.tscn`.

The Build 8 movie and final worker delivery are the independent critic’s 60 Hz scene captures. Compact and tall comparison movies are independent crops of the gait author’s actual Godot recordings. Full-size ordinary field frames were used to judge visibility, and the native joint/skin measurements were collected separately by the critic.
