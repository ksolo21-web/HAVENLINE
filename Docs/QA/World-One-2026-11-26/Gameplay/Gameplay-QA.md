# World One gameplay

[Watch the chaptered gameplay highlights with sound](World-One-Gameplay.mp4) · [Watch the pine and quarry return](Resource-Regrowth.mp4)

The progression movie and gallery use the recorded entry `res://field_opening.tscn` at `e978a44b1b112bb598f9ec1724b3616ec80e6970`. The full touch-driven run lasted **293.52 seconds**. It began on an empty disposable save and checked 17,612 consecutive 60 Hz physics samples. The recorded source was compared byte-for-byte with the frozen Git objects and its imported resources were hashed. One-finger joystick controls drove the player. Proximity, physical weapon contact and the visible gate buttons triggered interactions.

The highlights retain 28.42 seconds at native 1280 × 720 and 24 fps. Each chapter is a continuous run of original gameplay frames and its matching stereo game mix. The progression chapters belong to one run. Two labeled closing chapters show wood and stone regrowth during a separate natural wait on the same build. The editor removed waits and repeated travel and added bottom-left labels. Every cut matched its original sound on both channels, with a lowest waveform correlation of 0.972. No game-state, field position, enemy spawn probability or simulation clock was overridden.

| Reel time | Action |
| ---: | --- |
| 0.00 s | Fresh snowfield |
| 0.58 s | Axe bites the pine |
| 1.96 s | Pick strikes the quarry |
| 3.29 s | Wild wolf encounter |
| 4.71 s | Alpha wolf encounter |
| 6.71 s | Earned logs buy the hearth |
| 7.83 s | First camp expansion |
| 8.75 s | Starter storehouse and timber bay |
| 9.75 s | Reinforced storehouse and stone bay |
| 10.71 s | Advanced storehouse and food bay |
| 11.67 s | Reserved southeast corner |
| 12.04 s | Second expansion |
| 13.08 s | Building the eastern watchtower |
| 14.29 s | Watchtower bolts at the eastern threat |
| 16.33 s | Pay for the three-axe upgrade |
| 16.79 s | Three purchased axes at rest |
| 17.83 s | East gate to snow |
| 19.21 s | Tracks beyond 100 metres |
| 20.21 s | East gate to safety |
| 21.58 s | South gate to snow |
| 22.92 s | South gate to safety |
| 24.25 s | Separate fresh run - Wood regrows in the field |
| 26.33 s | Separate fresh run - Stone regrows in the field |

## Earned progression

The player paid for the hearth, first fence expansion, three tiers of the northwest storehouse, second fence expansion, eastern watchtower and additional axes. The eight receipts consumed **18 wood, 8 stone and 2 meat**. Unique collected resource tokens matched carried units, stored units and recorded spending on every observed tick. The player entered the same northwest building after each upgrade. The left side of the apron accepted deliveries and the right side accepted construction materials. The shelves showed a bundled stack of wood, up to two stones and up to seven cuts of meat, each with a numeric balance. The southeast bay remained reserved and the player walked through it.

| Offer | Unedited simulation time |
| --- | ---: |
| center hearth | 31.43 s |
| expansion 1 | 112.38 s |
| storage wood | 118.27 s |
| storage stone | 135.65 s |
| storage meat | 152.90 s |
| expansion 2 | 189.15 s |
| watchtower | 193.48 s |
| orbit upgrade | 197.32 s |

## Boundaries, travel and combat

| Paid stage | Gate | Direction | Unedited run time | Offset from gate center | Orbit before / after crossing |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | south | out | 35.38 s | 0.11 m | off / on |
| 1 | south | in | 102.27 s | 0.02 m | on / off |
| 1 | east | out | 106.73 s | 0.01 m | off / on |
| 1 | east | in | 108.72 s | 0.05 m | on / off |
| 2 | east | out | 174.96 s | 0.06 m | off / on |
| 2 | east | in | 176.66 s | 0.05 m | on / off |
| 2 | south | out | 182.45 s | 0.04 m | off / on |
| 2 | south | in | 184.43 s | 0.05 m | on / off |
| 3 | east | out | 201.02 s | 0.06 m | off / on |
| 3 | east | in | 279.68 s | 0.02 m | on / off |
| 3 | south | out | 285.19 s | 0.05 m | off / on |
| 3 | south | in | 287.02 s | 0.05 m | on / off |

The route reached **100.8 m from the hearth** and returned through the eastern gate. The player rested the axes inside the paid court and used all three outdoors. Across the full recording, the observer found 0 indoor orbit samples and 0 hostile centers within a paid court. The watchtower fired 16 actual projectiles and recorded 14 confirmed hits. Native track samples included up to 52 boot marks and 104 paw marks. The largest number on the paid floor was 0.

The standalone renewal and combat movies were recorded on gameplay checkpoint `34df87a8195553c4636aa374ac3bfc11054a3bbd`. The corrected release changes one runtime script, the high-load backpack presentation and its visible transfer endpoints. A fresh low-load return-scene test on the recorded release verified the affected interactions. The two renewal cuts appended to the progression movie were re-recorded on its own release. [Per-film source and compatibility checks](Evidence/Media-provenance.json) · [Source manifest for the two standalone films](Evidence/Standalone-recorded-source.json)

The separate renewal film uses a fresh profile. The player physically depleted the starter pine and rock, stayed within sight of each source and waited through their configured 5- and 32-second play timers. The tree chapter shows the two preliminary recoils, fall and return at normal speed. The quarry chapter shows the end of the longer wait. [Frame and sound timings](Resource-Regrowth.json)

Two separate fresh runs recorded real wolf attacks. The unpaid adventurer returned to the first hearth plot at (0, 2.4). The paid adventurer carried 3 earned wood into a live pack and returned inside the protected perimeter at (1.72, 1.8). Health reached zero and returned to four after 1.05 seconds. The inventory, paid receipts and storage matched on either side of recovery. The on-screen health bar followed each hit. [Watch the unpaid and paid wolf encounters and recoveries](Combat-and-Recovery.mp4) · [Tick-level evidence](Evidence/Gesture-and-recovery.json)

The scene used the normal production encounter table with a fresh random seed on each run. The verified main run saw 3 distinct alpha IDs across its surrounding chunks. [Ordinary wolf](Evidence/Ordinary-wolf.jpg) · [Alpha wolf](Evidence/Alpha-wolf.jpg)

## Failures and limits

The earlier 34df87a8 checkpoint failed the high-load camera check when the wood column ran off the top of the picture near a gate. The corrected release passed the repeated 3, 12, 37 and 42 wood checks and the separate 67-wood gate crossing. The backpack still presents a tall stack for large hauls and limits the number of visible items as it nears the top of the gameplay camera. The material counter preserves the full carried quantity. [Native 3/12/37/42 load comparison and gate crossing](Evidence/high-load-route/High-load-evidence.md)

## Native frames and save verification

[Furnace before and after](Evidence/Opening-and-hearth.jpg) · [Storehouse exterior and interior at each tier](Evidence/Storehouse-tiers.jpg) · [All 12 gate crossings](Evidence/Gate-crossings.jpg) · [Stage 1 south out](Stills/Landscape-4K/stage-1-south-out.png) · [Stage 1 south in](Stills/Landscape-4K/stage-1-south-in.png) · [Stage 1 east out](Stills/Landscape-4K/stage-1-east-out.png) · [Stage 1 east in](Stills/Landscape-4K/stage-1-east-in.png) · [Stage 2 south out](Stills/Landscape-4K/stage-2-south-out.png) · [Stage 2 south in](Stills/Landscape-4K/stage-2-south-in.png) · [Stage 2 east out](Stills/Landscape-4K/stage-2-east-out.png) · [Stage 2 east in](Stills/Landscape-4K/stage-2-east-in.png) · [Stage 3 south out](Stills/Landscape-4K/stage-3-south-out.png) · [Stage 3 south in](Stills/Landscape-4K/stage-3-south-in.png) · [Stage 3 east out](Stills/Landscape-4K/stage-3-east-out.png) · [Stage 3 east in](Stills/Landscape-4K/stage-3-east-in.png)

[Fresh snowfield](Stills/Landscape-4K/01-unpaid.png) · [Struck quarry](Stills/Landscape-4K/03-mine.png) · [Regular wolf](Stills/Landscape-4K/04-wolf.png) · [Alpha wolf](Stills/Portrait-4K/04-boss.png) · [Completed first camp](Stills/Landscape-4K/05-built.png) · [First expansion](Stills/Landscape-4K/06-expansion-one.png) · [Starter storehouse](Stills/Landscape-4K/house-tier-1.png) · [Timber interior](Stills/Landscape-4K/house-interior-1.png) · [Reinforced storehouse](Stills/Landscape-4K/house-tier-2.png) · [Stone interior](Stills/Landscape-4K/house-interior-2.png) · [Advanced storehouse](Stills/Landscape-4K/house-tier-3.png) · [Food interior](Stills/Landscape-4K/house-interior-3.png) · [Second expansion](Stills/Landscape-4K/10-expansion-two.png) · [Tower rising](Stills/Landscape-4K/11-watchtower.png) · [Completed tower firing](Stills/Landscape-4K/tower-fire.png) · [Upgraded axes rested indoors](Stills/Landscape-4K/12-axes-rest.png) · [Active axes outside](Stills/Landscape-4K/13-outer-snow.png) · [100 m expedition](Stills/Landscape-4K/100-metre-excursion.png) · [Returned camp](Stills/Landscape-4K/14-final-court.png)

The earned camp has warm packed ground inside the timber fence. Both open gates lead to pale snow, with boot and paw marks visible outside. Progression stills in landscape are original 3840 × 2160 gameplay readbacks. The selected vertical shots are original 2160 × 3840 gameplay frames at internal 3D scale 1.0. Matched 3840 × 2160 landscape and 2160 × 3840 portrait readbacks show the two-finger gesture at default, closest and restored zoom. [Landscape default](Stills/Landscape-4K/default-camera.png) · [Landscape 2×](Stills/Landscape-4K/closest-camera.png) · [Landscape restored](Stills/Landscape-4K/restored-camera.png) · [Portrait default](Stills/Portrait-4K/default-camera.png) · [Portrait 2×](Stills/Portrait-4K/closest-camera.png) · [Portrait restored](Stills/Portrait-4K/restored-camera.png). Capture used Godot 4.7.2, OpenGL Compatibility and Mesa llvmpipe with native 3D scale 1.0 in offline recording mode. Physical phone performance remains unverified.

A fresh process loaded the actual final save, restored paid stage 3, both gates, the operational watchtower, 3 purchased axes and the exact typed receipts and balances. [Fresh-process reload](Evidence/Fresh-process-reload.json) · [Gameplay results](Evidence/Gameplay-route.json) · [Every physics sample](Evidence/Physics-observations.jsonl.gz) · [Snapshot and imported resource hashes](Evidence/Recorded-source.json) · [Native framebuffer and HUD readbacks](Evidence/Native-gameplay-readbacks.json) · [Stereo source correlation](World-One-Gameplay-audio.json) · [Full decoded media scans](Evidence/All-frames-decode.json) · [Gameplay contact sheet](Evidence/World-One-Gameplay-storyboard.jpg)

[Separate apron visits, door travel and physical shelves](Evidence/Storage-house.json) · [Chop reactions and resource timers](Evidence/Harvest-effects.json).
