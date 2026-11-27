# Character 1 at the Level 1 gameplay camera

The independent critic rated Character 1’s gameplay run **9.9/10** and the complete exported rig **9.5/10**. The registered toe patches traveled 1.0–3.4 mm across seven ground contacts. Across 26 additional stops and releases, all 4,264 left/right observations kept the knees forward. [Independent review](../Rig-review/Read-the-rig-review.md)

The original compact Character 1 still runs at 6.25 m/s. The revised animation takes shorter steps and lifts the heel behind the body before bringing it forward. At the source gate heading the character’s forward boot now spends less time ahead of the coat. Both normal and 2× views use the playable character and touch controller. [Watch the source and the two gameplay revisions](Gate-run-and-Character-1.mp4) · [View consecutive stills](Matched-game-camera.jpg) · [Watch the full gameplay screen at both zooms](Character-1-before-and-after.mp4)

| Measured during straight travel | Previous public Build 9 | Revised Build 10 |
| --- | ---: | ---: |
| Speed after acceleration | 6.25 m/s | 6.25 m/s |
| Steps per minute | 221 | 287 |
| Maximum forward thigh pitch in the input probe | 73.5° | 42.0° |
| Heel crosses forward of same-side hip after contact | 78–79% of stride | 88–92% |
| Median speed of the supported tread in the input probe | 87 mm/s | 13 mm/s |

The two builds share the original geometry, eyes, glasses, coat, boots, texture and joint hierarchy. FieldRun uses revised leg and pelvis curves. The inner boot fasteners now follow the existing rigid shaft so each silver circle stays seated in its leather tab. The material UVs and mesh triangles are preserved. [Boot detail through the heel lift](Boot-fastening-comparison.jpg)

The game drives playback from actual ground travel. During a stop the planted ankle target can move across the previous knee line. Selecting the forward side of the knee bend keeps the joint pointing along the body through the transfer. The game also pivots a hit reaction about the actual contacting tread. During the deterministic side-hit test the body tilted about 19° and the lowest boot stayed within 0.01 mm of the snow. [Normal-input measurements](Run-controls.json)

## What the reference actually shows

The public blue-tree Whiteout Survival ad matches the owner’s B recording at the camp and both field sections. The owner’s archived clock is about 0.47–0.50 seconds later. At 30 fps the open-snow and camp-exit runs show about six or seven frames per alternating step. That corresponds to roughly 257–300 steps/min. Registered ground movement at native frames 412–423 is about +10 pixels across and −2 pixels up per frame. The new game comparison runs within about two degrees of that heading. The character’s coat and mitts overlap its boots in several frames, so exact source knee angles cannot be read from these images. [30 consecutive gate frames](Reference-B-gate-run.jpg) · [Source video](https://www.sprites.ai/whiteout-survival-ads/ad/1133260751579588)

At this heading the upper 10% of horizontal ankle separations in the intermediate run were about half an upright character height. In the shorter run they were about 0.44 height, with fewer sustained wide separations. These are actual projected in-game ankle pivots. Boot silhouettes still differ with the two characters’ coat cuts and boot sizes. [Camera measurements for both zooms](Camera-ankle-envelope.json)

## Anatomical comparison and reconstruction

The 2017 paper reports 28 runners. The public v5 release lists 39 participant files, of which 31 include a 4.5 m/s raw marker recording. Six had incomplete coverage with this marker definition. The resulting 25 subject medians represent 1,114 complete strides at 150 Hz. After contact the heel passed the pelvis at a median 91% of the stride, with subject deciles of 87–95%. The group median thigh-marker excursion was about −22° to +49°. The revised character reached about −21° to +42°. The source marker and game joint are different landmarks, and camera-visible timing guided the final cadence. [Source IDs, exclusions and measurements](Human-running-markers.json) · [Fukuchi et al.](https://doi.org/10.7717/peerj.3298) · [Data release](https://doi.org/10.6084/m9.figshare.4543435.v5)

The authoring solve protects the loaded tread and checks the complete heel and toe during release. The second stage shortens horizontal travel, aligns the supported material’s backward velocity with world travel, and fits the knee and hip into their available range. The three stages regenerated the final GLB byte for byte from the published Build 9 GLB. Set OPENBLAS_NUM_THREADS=1. Run rebuild_recovery.py with the Build 9 GLB and an intermediate destination, followed by shorten_stride.py with that intermediate and a short-stride destination, then fit_boot_tabs.py with the short-stride GLB and final destination. All three scripts use NumPy and SciPy. [Recovery solver](Authoring/rebuild_recovery.py) · [Stride and contact solver](Authoring/shorten_stride.py) · [Boot attachment solver](Authoring/fit_boot_tabs.py) · [Leg and foot-contact constraints](https://runevision.com/thesis/) · [Footplant cleanup](https://research.cs.wisc.edu/graphics/Papers/Gleicher/Mocap/cleanup.pdf)

The capture manifest records the rig and controller hashes, the distinct frame counts at each zoom, and the encoded movie checksums. [Capture manifest](Run-evidence.json)
