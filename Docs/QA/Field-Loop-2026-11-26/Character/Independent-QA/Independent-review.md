# Character 1 gait review

**Independent score 8.7/10. The walk and run pass steady-motion checks. The 9/10 rig release gate remains open because starts and stops can drag a planted boot, and some clothing surfaces still intersect.**

At the normal camera distance, the character transfers weight between boots and the opposite arm comes forward with each step. The zoomed view makes toe release and the difference between walk and run easier to see. The face, glasses, collar, belt and cuffs retain a coherent silhouette in the sampled field route. The pivot is smooth through the torso, but the feet can briefly bunch or twist during a rapid change of direction.

[Gameplay camera board](Gameplay-camera.jpg) · [Timed native pose playback](Camera-motion.webp) · [Game movement and contact measurements](Game-contact.json)

### Boot contact and turning

The test sent movement input into the field scene at 60 physics ticks per second. One continuous walk, run and hard reversal was recorded at each zoom. A second sweep repeated a run-to-reverse-to-stop sequence at five different phases in the running stride. It followed 174 actual boot vertices after the engine applied its leg corrections.

| Behavior | Result |
|---|---|
| Steady walk | 1.12 m/s and 128 steps/min in the contact test. The median speed of near-ground sole points was 0.007 m/s. |
| Steady full-speed run | 2.80 m/s and 173 steps/min. The median near-ground sole speed was 0.021 m/s. Both boots clear the ground together for about 13% of the authored run cycle. |
| Forefoot flex | Relative to a rigid shoe pivoting only at the ankle, toe deformation moved the visible forefoot up to 28.4 mm walking and 26.2 mm running on both sides. |
| Starts and straight acceleration | During the initial pivot into a walk, the same near-ground patch traveled up to 19.3 cm in 0.10 s. Once aligned, accelerating into the run gave 1.2 mm under that test. |
| Hard reversal | Worst patch movements for the five tested stride phases were 7.3, 85.0, 0.2, 0.2 and 74.3 mm. At the first phase, the earlier controller gave 180.4 mm. |
| Braking to idle | The same test gave 80.7, 122.2, 1.9, 200.6 and 0.9 mm. The timing of the stop still determines whether the planted foot holds. |
| Ground and knee tracking | The deepest sampled sole dip was 0.8 mm, reduced from about 16 mm at startup in the preceding controller. Ankles stayed separate in the measured turn. At one phase their lateral separation narrowed to 23.5 cm and the right knee passed 17.7 mm inside its projected hip-to-ankle line. |

A patch qualified only when at least three identical skinned vertices stayed within 5 mm of the floor over seven consecutive frames. The reported distance is the largest median horizontal movement of such a patch. The actor's maximum movement speed remained bounded at 2.8 m/s during the tested reversals. A pivot or stopping step that releases the trailing boot before the torso turns would address the remaining drift.

### Authored animation and clothing

The 1.75 m rig has 50 joints and three in-place loops. Idle runs for 1.00 s, Walk for 0.933 s and Run for 0.733 s. Each starts at time zero and closes within 0.001 mm on the actual skin. The spatial steering and translation come from the game. The source and export retain all 12,656 unique normalized positions, 25,264 triangles and three texture images.

I checked all three loops from six directions, evaluated the skinned mesh at 120 Hz and tested visibility at 40 Hz using the direction of the gameplay camera and three actor headings. Two visible-surface defects are small in the normal game frame. At 0.225 s in Walk, a 20.3 mm crossing lies under the front belt pouch and hem. At 0.075 s in Run, a 14.7 mm crossing sits on the flexed trouser leg above the boot cuff. At the worst-count poses, the mesh gained 11 intersecting triangle pairs in Idle, 109 in Walk and 202 in Run relative to its original rest surface. Multiple pairs can describe a single crease. A local weighting repair reduced the strain on a previously overstretched rear-trouser edge from 3.25× to 1.30×. The garment still has localized excess stretch elsewhere.

[Marked garment details](Anatomy/surface-details.jpg) · [Full part-by-clip ledger](Anatomy/ledger.json) · [Idle](Anatomy/Idle.jpg) · [Walk](Anatomy/Walk.jpg) · [Run](Anatomy/Run.jpg)

### Reference and revision

The retained A and B recordings establish the camera-follow view, loaded travel and stop at a purchase pad. Their cargo obscures limbs, and the denser transfer intervals do not show two identifiable complete empty-handed running cycles. The contact measurements above establish behavior in this build. The original videos do not establish exact unloaded cadence, a hard 180° pivot or a verified pinch gesture. [Reference recordings and extraction ledger](../../References/Locked-sequences/README.md)

Reviewed GLB SHA-256 `dfe7c0a3695ac680b513c9a19e69e3a2685770ed2367e1f3a71a8fdd3d62f07e` and movement controller `22838c607dea79ffb8195abebdc5f4aa16f099823c5db78f89cb34b4d8b22fc0` in Godot 4.7.2, scene `res://field_opening.tscn`. This review covers character locomotion. Phone performance, facial acting, hand articulation during tool use and the combat attack clip were outside its scope.
