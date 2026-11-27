# Character 1 in the Level 1 playtest

The frozen private playtest is at commit `ec989c640233e71ee86dd57e43076e2e932d612a` in scene `res://field_opening.tscn`. The Character 1 GLB has SHA-256 `cc2126f99b78673bc334da8c4ab111ac6fa568dbe241d9518a09ed0298dc823d`. Fourteen native movement checks passed. The fleece cuff still loses visible thickness at peak flex, so the run remains under visual review.

[Watch the default and pinch-zoom comparison](Character1-run-comparison.mp4) · [View one stride at pinch zoom](Character1-contact-through-one-stride.jpg) · [Hear the actual in-game snow footsteps](Snow-boot-Foley.wav)

## What changed

Character 1 starts running from either a short or full touch drag, reaches 6.25 m/s, leans through direction changes and stops in 0.39 m after release. Build 6 ran at 7.0 m/s. The orbit and locomotion systems drive the run by distance traveled. The sole can roll from heel to toe during support.

Both boots cleared 1 cm of snow for 62.4% of the steady run in build 6. That fell to 43.0% here. The highest simultaneous gap fell from 9.92 cm to 3.43 cm at 120 Hz. The independent reviewer followed the same material points throughout each plant and measured 1.9–3.3 cm of movement. A discarded version dragged its recovering toe up to 44 cm across the snow.

The scene stamped nine prints for nine observed landings. Each began beneath the actual tread within 4.8 mm of the snow. Footstep sounds use the left and right sole contacts. The three snow samples played in rotation during the real-time mixer capture. The late sound that previously occurred after the player had settled was absent in the frozen run.

## Reference comparison

The locked A shot at 12.00–12.40 seconds moves about 3.3 character heights per second before the carrier slows. This build measures 3.26 at normal zoom and 3.28 at 2× along its corresponding diagonal. The faster B shot at 13.00–13.50 seconds moves about 4.7 character heights per second. The corresponding lateral run measures 4.02 here. A single world speed preserves the requested slower feel across headings. The reference pack obscures the far boot, so its exact airborne fraction cannot be recovered. [Source frames and hashes](../Rig-review/Reference-source.json)

## Remaining visual defect

The four metal eyelets retain their two-axis dimensions across FieldRun, Run, Walk and Idle. The source textures and the original character surfaces passed the topology check. The cream trim still compresses to about 43% of its original median surface area at maximum FieldRun flex. The reviewer also found a 22.5 mm exterior overlap at the rear. A separate repair is being tested against the original triangles. [Hardware map](Boot-hardware-map.json) · [Independent rig evidence](../Rig-review/)

## Technique for the team

Measure the left and right boot surfaces in world space while the character actually travels. Look at heel contact, toe release, swing clearance and movement of the same patch through its whole plant. A passing average can conceal a scuff. Preserve supported foot locations while changing swing silhouette or garment response. Inspect natural braking and turns through the gameplay camera and at maximum pinch zoom. [Johansen, footbase and footskate](https://runevision.com/thesis/) · [Kovar, Schreiner and Gleicher, footplant cleanup](https://research.cs.wisc.edu/graphics/Gallery/kovar.vol/Cleanup/) · [Epic Games, pose warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/pose-warping-in-unreal-engine)

The movie uses the actual Linux game and touch path at normal playback speed, with the same open-snow route on build 6 and this candidate. The capture uses a 60 Hz simulation and a 20 fps comparison file. The telemetry, reviewed script hashes and per-frame positions accompany it. Physical Galaxy Z Fold 7 frame pacing and 4K output require a device measurement. [Run measurements](Run-measurements.json)
