# Character 1 gait and rig

**Independent score 9.1/10. Idle, walking, running and the protected turning and stopping steps pass at the normal gameplay camera and at 2× pinch zoom.** In the running about-face, you can see one boot take weight while the other steps around. The former sideways kink between knee pad, fur cuff and boot has cleared in the poses where it was easiest to see. The last swing in a hard turn is still wide and quick, especially at 2×.

[Game-camera playback at real time](Camera-motion-real-time.webp) · [One-third-speed playback](Camera-motion-slow.webp) · [Normal camera](Gameplay-1x.jpg) · [Pinch zoom](Gameplay-2x.jpg)

### What was tested

The candidate is the 1.75 m Character 1 mesh with 50 joints and three in-place clips. Idle lasts 1.000 s, Walk 0.933 s and Run 0.733 s. Both the real-time input tests and camera captures used Godot 4.7.2 in a disposable copy of the field opening. They exercise the tested game camera, character and motor. The gameplay stills document character movement in that test scene. The release route provides evidence of the finished level art.

| Measurement | Result |
|---|---|
| Steady travel | Walk measured 1.117 m/s and 128 steps/min. Run measured 2.80 m/s and 173 steps/min. The median near-floor boot-vertex speeds were 0.006 m/s and 0.021 m/s, respectively. |
| Feet and weight transfer | Both shoes showed real forefoot bend, up to 28.4 mm in Walk and 26.2 mm in Run relative to locking the toe joint. Heel lift, swing and alternating support remain visible. |
| Startup, acceleration and brake | A held patch moved 0 mm to the precision of the early 0.10 s window. The later step from the starting pivot into ordinary walk reached 14.4 mm. Aligned Walk to Run reached 1.2 mm in a later window. |
| Full reversals | Five running entry phases produced early maxima of 2.4, 0.0, 0.0, 0.0, 0.0 mm. The five walking entries gave 0.0, 0.0, 0.0, 0.0, 2.1 mm. Across 100 ticks, including the return to the authored motion, the largest windows reached 3.7 mm in running turns and 14.9 mm in walking turns. |
| Smaller steering changes | At full running speed, the early contact-window displacements for +18°, +35° and −65° were 1.5, 1.2 and 1.2 mm. On stopping after −65°, a sole vertex dipped 4.0 mm for a single 60 Hz frame. At the normal camera I could not see a boot sink through the snow. |
| Knees and opposite legs | In the previously failing walking pose, the grounded right knee deviation from the front-view hip-to-ankle line improved from 140 mm to 17 mm. The full sweep found up to 46 mm projected inward on a supporting leg and about 71 mm in swing. Front, rear and oblique textured views showed continuous boot, cuff and knee alignment. No opposite boot/boot or boot/lower-leg triangle intersection occurred in 4,000 post-correction poses across ten runs. |

The sole test tracked 174 actual skinned vertices. A held patch counted when the same three or more vertices stayed within 5 mm of the floor for seven consecutive 60 Hz samples. Distances are the largest median horizontal movements over those six tick intervals. The five entry offsets were 0, 9, 18, 27 and 36 ticks. Short movement of a near-ground toe patch during roll-off does not imply the entire support shoe moved that distance. The hard turns are energetic: the fastest measured toe point reached 14.1 m/s across a broad swing, without the one-frame foot teleport seen on an earlier controller.

[Matched knee poses](turn-knees.jpg) · [New extreme poses](turn-knees-extrema.jpg) · [Movement measurements](Movement-summary.json) · [Detailed phase and cadence data](Support-motion.json) · [Per-frame opposing leg surface test](Boot-collision.json)

### Character surface and references

All 25,264 source triangles, all 12,656 unique shape positions after uniform scale and recentering, and the three texture images are preserved. The maximum source-to-export position difference after alignment was under 0.0002 mm. The front, rear, both sides and both three-quarter views cover nine phases per supplied clip. Full-surface checks sampled at 120 Hz. Remaining exposed intersection lengths reached 1.17 mm at the rear waist in Walk and 1.77 mm there in Run. A fold on the plain blue parka side locally stretches from 13.5 to 41.1 mm under arm motion. The textured surface stayed continuous there. The inner-shin edge that previously grew from 9.6 to 76.2 mm now reaches 14.5 mm at the same running pose.

[Idle](../V12-surface/Idle.jpg) · [Walk](../V12-surface/Walk.jpg) · [Run](../V12-surface/Run.jpg) · [Marked skin closeups](../V12-surface/strain-details.jpg) · [Source preservation](../V12-surface/preservation.json)

The recovered source sequences show a compact character approaching and stopping at pads under a fixed elevated camera. At A 12.20 s and B 13.20 s the carried load hides much of the body. Those shots support the camera and approach comparison. The measured foot cadence, unloaded 180° turns and pinch inspection come from this build’s own movement tests. Independent finger articulation, a root-motion export, mobile hardware performance and other engines fall outside this character-gait score.

[Reference sequences A and B](../../../References/Locked-sequences/README.md)

### Reproducing the review

The photographed and scored build was `1e3529b33578db43f32c42fe845f0482653e8f4d`. I independently rehashed the character GLB and gait motor in successor `994ace861fbf132c5924bacc320f5608d75d9187` and verified both files are byte-identical. The 9.1/10 movement rating carries forward. The successor changes mine-adjacent tree placement, stock-plot paint and their environment regression test.

- Verified Git source commit is `1e3529b33578db43f32c42fe845f0482653e8f4d`. The archived GLB and motor match the two hashes below. Project directory `HavenlineLevel1`.
- Character SHA-256 is `4491c830fce1b2f5ca455dd0c853d46fe94b6d1996bb71173977b48fad330ee5`. [Reviewed GLB](../../Character-1.glb)
- Motor SHA-256 is `16b75a225da3e8784c84221b8466724fa7238e07467ef341647a8a83f966105d`. Scene `res://field_opening.tscn`.
- The saved rig-critic skill's official Python verifier was unavailable from its resource URI. The accompanying independent verifier implements the published ledger checks for candidate bytes, joint and clip inventory, 397 required checks, evidence files, scores, and per-row pass flags. Run `python ../V12-surface/validate-ledger.py ledger.json` from this report’s directory. [Reviewed ledger](ledger.json) · [Verifier output](Gate-result.txt)
- The V9 review and the V12 motor with the knee defect remain available. [V9 review](../Independent-review.md) · [Earlier V12 movement review](../V12-3b019100/Review.md)
