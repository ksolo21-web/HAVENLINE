# How Character 1 takes a running step

In Build 8, the standing leg dropped into a deep squat soon after touchdown. Then the trailing foot tucked under the coat early and stayed there. The new motion keeps the foot rolling on the snow as the leg extends. The knee folds progressively once the toe leaves the ground, then the shin opens ahead of the next contact. [Compare the complete knee curves](Knee-through-one-stride.png)

## What the reference footage shows

Three complete Whiteout Survival ads were decoded at their recorded frame rates. Ads 0 and 1 are 360×640 at 30 fps. Ad 3 is 1080×1920 at 24 fps. The overviews contain one frame every second of each ad. In the free run, ad 1 at 7.47–8.30 s, the outgoing boot clears the hem, returns under the hips, and swings out again. The visible silhouette repeats after about 0.53–0.60 s. This camera, coat and body size obscure the knee itself. The forty-five consecutive frames preserve each change in the exposed shoe at the original recording rate. [Watch the 30 fps crop](Whiteout-free-run-7.00-8.50.mp4) · [Every consecutive frame from 7.000 to 8.467 s](Ad-1-first-run-consecutive.jpg)

The original A/B recording identities are archived. Their complete MP4 masters were unavailable in this workspace. The surviving locked clips preserve 10 fps crops. Shot A at 12.00–12.40 s moves about 3.2–3.3 projected character heights per second diagonally. Shot B at 13.00–13.50 s moves about 4.7–5.0 laterally. The spread reflects estimates of the actor’s partly hidden height. They show the pace of the loaded carrier. The independent review uses these recovered images alongside the complete supplemental ads. [Ad 0, every second](Whiteout-ad-0-seconds.jpg) · [Ad 1, every second](Whiteout-ad-1-seconds.jpg) · [Ad 3, every second](Whiteout-ad-3-seconds.jpg) · [Full source provenance](Recorded-ad-frames.json)

## What natural knee motion contributes

The lab comparison uses the median of 31 available right-leg trials recorded at 4.5 m/s in the public Fukuchi, Fukuchi and Duarte dataset. These are measured human angles across 101 normalized points in a stride. The player travels 6.25 game metres per second with deliberately different proportions. The lab measurements guide the **order** and **shape** of the visible bend. The native gameplay checks track the skin and sole after the engine blends, turns and brakes the character. [Peer-reviewed study](https://doi.org/10.7717/peerj.3298) · [Original kinematic dataset](https://doi.org/10.6084/m9.figshare.4543435) · [Median human measurements](Human-running-data.json)

| Point in authored stride | Human median | Build 8 | Revised player |
| --- | ---: | ---: | ---: |
| 15% | 44° | 42° | 43° |
| 40% | 22° | 74° | 25° |
| 45% | 41° | 93° | 45° |
| 50% | 64° | 106° | 68° |
| 65% | 119° | 111° | 119° |
| 80% | 89° | 48° | 84° |
| 85% | 66° | 28° | 61° |

Zero degrees means a straight knee. In the game traces, hip–knee–ankle positions determine the flexion angle. The lab records sagittal joint flexion. The curves use their respective recorded stride starts. Aligning the native game trace to the descending boot produces a small phase shift. Its full held-contact cycle measured 42.5° while loading, 14.7° at push-off and 118.7° during recovery. The heel rose 14.4 cm above the toes late in support. Both boots cleared the snow by a maximum of 3.81 cm together in this 60 Hz run. All 15 normal-input tests passed, including redirection and stopping. [Exact native results](Run-controls.json) · [Authored curves](Authored-leg-curves.json)

## Two playable Character 1 designs

The compact player matches the latest 18617 turnaround with its rounded gloves, shorter limbs and belted blue parka. It earned 9.5/10 in independent review and remains the playable default. The taller Winter Welcome A character earned 9.0/10. In a matched field run, its longer shin makes the rear leg easier to see below the coat. Its hands open wide on rear views around 1.40–1.73 s. [Watch the normal-zoom comparison](Character-1-normal-zoom.mp4) · [Previous Build 8 run](../Rig-review/Build-8-player-and-worker-60fps.mp4)

The synchronized film includes all 144 consecutive recorded samples at 30 fps. It covers acceleration, a change of direction and stopping at each gameplay zoom. Each 450×800 game capture is preserved at its original pixel dimensions. The lower inset enlarges the moving character. [Watch both camera distances](Character-1-running-options.mp4) · [Compare the 2× stride sequence](Character-1-stride-comparison.jpg) · [Capture settings and checksums](Movie-sources.json)

The controlled comparison uses the same open-snow Level 1 field, touch input, gameplay camera and 1.75 m standing height. Resizing the real tall master to this height places its hip at 0.778 m. The compact hip sits at 0.600 m. The tall and compact knee-to-ankle segments measure 0.371 m and 0.235 m respectively. During the lateral run they project to median lengths of 11.6 and 7.5 pixels at normal zoom, and 23.4 and 15.0 pixels at pinched zoom in the 450×800 capture. The tall master contains 727,442 triangles. Its phone frame pacing is unmeasured. [Original rig measurements](Rig-proportions.json) · [Gameplay projection](Camera-proportions.json) · [Tall comparison rig](Authoring/winter_welcome_comparison.gd)

In the independent 210-tick tall replay, swing clearance reached 18.3 cm and simultaneous flight reached 5.69 cm. The compact measured 12.9 cm and 3.81 cm. A continuously supported patch of the compact tread drifted 1.9–3.2 cm within a 6 mm band above the snow. Tall drift measured 2.9–5.0 cm with a 9 mm contact band. These different contact tolerances limit direct comparison. [Independent tall tread test](../Rig-review/Taller-A-native-physical-trial.json) · [Compact tread test](../Rig-review/Compact-V7-planted-material.json)

## How the rig is checked

Measure the heel and toe against the underlying surface. A foot stays registered against the snow as the shoe rolls. A short-armed or short-legged model needs its own contact reach. Moving its hips downward to make a foot touch can cause an excessive squat. Examine the complete flight path after release, particularly the first half of knee folding and the last quarter of knee extension. Four correct key poses can still interpolate into the wrong motion. Review both uncovered and loaded running through actual touch controls. [Johansen, footbase](https://runevision.com/thesis/) · [Kovar, Schreiner and Gleicher, footplant constraints](https://research.cs.wisc.edu/graphics/Gallery/kovar.vol/Cleanup/)

The final Level 1 source commit is `17abe3795bb91e6a80b48d93bab7578ad2ad4aed`. The exported project reproduced all 15 touch and grounding results. The independent reviewer measured a full-cycle knee-curve deviation of 6.6° against the human median, down from 30.3° in Build 8. The tested character asset has SHA-256 `e165a24b6b1205904165e0f1aad643c2fc2e00152df5d58de218e7ca7e375eff`. These measurements use the normal Godot Level 1 simulation on Linux. Physical phone frame pacing needs a separate device measurement. [Independent review](../Rig-review/Read-the-rig-review.md)

## Rebuilding the animation

The authoring script reads the preceding approved Character 1 GLB, the median running measurements and the existing boot surface. It writes the corrected FieldRun clip into a new GLB. A fresh rebuild using Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0 reproduced the tested file byte for byte. Run these commands from a Havenline repository checkout with this report folder available. [Authoring script](Authoring/rebuild_running.py) · [Motion measurements](Human-running-data.json)

```bash
git show fbbbca916baa2d73e0f30b66a075ad7076e61dac:HavenlineLevel1/assets/characters/Character1Fresh.glb > /tmp/Character1-Build8.glb
python /path/to/Run/Authoring/rebuild_running.py /tmp/Character1-Build8.glb /tmp/Character1-rebuilt.glb
sha256sum /tmp/Character1-rebuilt.glb
```
