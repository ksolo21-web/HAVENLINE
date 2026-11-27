# Character 1 in the Level 1 playtest

The independent character rig review scored this exact model 9.5/10 across 1,392 checks. [Independent verdict](../Rig-review/Verdict.json)

The player runs at 6.25 m/s, with a visible flight phase, a planted sole on each step and a 0.39 m stop after releasing the control. Build 8 repairs the boot fleece that collapsed when Character 1 lifted his leg. This capture follows a touch-controlled run, direction change and stop at the normal gameplay zoom and 2× pinch zoom. [Watch the gameplay comparison](Character1-run-comparison.mp4) · [View one running stride](Character1-contact-through-one-stride.jpg)

## Comparison against the gameplay reference

The carrier in shot A moves about 3.3 character heights per second from 12.00 to 12.40 seconds. Character 1 moves 3.26 at normal zoom and 3.28 at 2× on the corresponding diagonal. The lateral shot B, from 13.00 to 13.50 seconds, moves about 4.7 character heights per second. Character 1 moves 4.02 at both zoom levels on that heading. Both comparisons use a single world speed. The far boot is hidden by the carried load in the reference, so the footage establishes visible rhythm and travel but cannot establish the exact contact time of both feet. [Reference sources and frames](../Rig-review/Reference-source.json)

## What changed on the model

The original left and right fleece rings now follow fitted garment joints. A separate joint guides each trouser hem inside its ring as the knee bends. The fasteners follow their corresponding ankles when the game adjusts the boots during a turn or stop. Their original four metal surfaces, fleece geometry and textures are retained. The complete trim counts 678 and 653 source triangles. Over four clips, 677 left and 652 right nondegenerate triangles were measurable. At the worst sampled pose, their median and tenth-percentile area equalled the standing area to the reported precision. The previous rig fell to roughly 46% median area on the same complete rings. [Compare the same moment on each model](Character1-boot-recovery.jpg) · [Download the exact tested GLB](Character1-reviewed.glb)

## Contact, movement and sound

All 14 native movement checks passed in the real Level 1 scene. At 120 Hz, both boots cleared 1 cm for 43.0% of the steady run, down from 62.4% in build 6. The maximum simultaneous gap fell from 9.92 cm to 3.43 cm. Complete support windows within 1 cm lasted about 158 ms, alternating with 108–117 ms of flight. Across full low-contact intervals, the same point on the tread traveled 1.9–3.3 cm. Character 1 left nine snow prints across nine observed landings, each beginning beneath a tread within 4.8 mm of the ground. [Native pose and gameplay measurements](Run-measurements.json)

Five steady footstep cues aligned to the alternating boot contacts within 9 ms in the 120 Hz trace. The separate real-time mixer recording contains eight footfalls and all three snow variants. [Listen to the live footstep recording](Snow-boot-Foley.wav) · [Inspect the eight audio events](Actual-boot-voices.json)

## Production notes

For similar rigs, track heel and toe material through their full contact window while the character travels. Check surviving motion blend and braking in the game camera after measuring each clip. Bright trim and mounted metal need their own surface checks during maximum knee bend, even when the sole stays planted. These methods follow the footbase and footplant work below. [Johansen, footbase and locomotion](https://runevision.com/thesis/) · [Kovar, Schreiner and Gleicher, footplant constraints](https://research.cs.wisc.edu/graphics/Gallery/kovar.vol/Cleanup/) · [Epic Games, pose warping](https://dev.epicgames.com/documentation/en-us/unreal-engine/pose-warping-in-unreal-engine)

Every one of the 516 files listed in the game manifest matched the tested source at commit `fbbbca916baa2d73e0f30b66a075ad7076e61dac`. Character 1 has SHA-256 `c13f1edad2329ac6b029a7fa7224bf05a6845c19640bb843fb635606d86c6701`. The comparison records normal-speed Linux Godot gameplay at a 60 Hz simulation rate, exported at 20 fps. Two further captures rendered the actual game at native 2160 × 3840 with Ultra active, a 1.0 scene scale and 4× MSAA. They show a running character at both camera zooms. Sustained 60 or 120 fps on a physical Galaxy Z Fold 7 still requires device measurement. [Tested source manifest](../Source/Reviewed-files.json)

[Open the full-resolution Ultra gameplay frame](Ultra-1x-2160x3840.jpg) · [Open the full-resolution 2× pinch frame](Ultra-2x-2160x3840.jpg) · [Frame settings and checksums](Ultra-native-frames.json)
