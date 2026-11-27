# Havenline Level 1 Android reference playtest

Open the private page on the phone, tap **Download Android APK**, and choose **Update**. Android version **0.3.4-reference-playtest** (build 5) starts in `res://field_opening.tscn`. Gameplay source is `8a8768438b3e9215a44f34e71a06cc54a55890f6` on the Level 1 trial branch. [Download page](https://havenline-level1-android-playtest.ksolo21.chatgpt.site) · [Controls](Play/README.md) · [Verified inputs](Source/Reviewed-files.json)

| What to try | What was measured |
| --- | --- |
| Drag a short distance, run across the snow, turn and release | Character 1 runs at 7.0 m/s, up from 2.8. Full stride is about 0.57 seconds. In the ordinary camera, lateral travel measures 4.45 projected character heights/s against approximately 4.7 in the reference. Diagonal travel measures 3.60 against approximately 3.3. He stopped within 0.36 m at eight different points in the stride. |
| Rescue the forester and follow his first delivery | The survivor matches the selected brown-haired, blue-coated character with the scarf and leather satchel. Both gloves hold the tool. He struck the trunk three times, picked up a real bundle, crossed the gate and delivered it to the shelf. |
| Look for the owl on the gatepost and outside camp | The folded and flying poses use the original Frostwing Pathfinder and Skybound Sentinel models. The owl wears its blue kerchief and pack. Its talons make contact during the strike. |
| Run through the middle of the starter warehouse | Nine meat bundles reached the FOOD shelf in 0.90 seconds from entering the apron in the signed-game test. A second diagonal approach delivered the meat and three wood bundles, kept three stone on the character and spent nothing on an upgrade. Both saves reopened with the same balances. To buy the upgrade, stop on the gold arrow at the right edge. |
| Use processors and purchase pads | Two meat bundles reached the cooker in 0.183 s, compared with about 0.208 s for the two fish in the reference. The cooker, saw and drill each received three inputs in 0.217 s. A 52-bundle mixed warehouse load took 0.883 s, down from 8.783 s. The tested tower and survivor purchases took 0.650 s each. |
| Use the gates with a running start | Both opened in both directions under touch controls with AI active. The orbiting weapon switched on outside and off inside on every crossing. |

## Alfred's footage

[Watch the previous and updated builds side by side](Views/Reference-playtest-comparison.mp4) for the run to the cooker, the processor intake and the starter FOOD shelf.

- [Compare the run with the reference footage](Views/Reference-run.mp4) · [Watch Character 1 run at normal and pinch zoom](Views/Character1-running-comparison.mp4) · [Inspect the turn and stop](Views/Character1-turn-and-stop.jpg)
- [Compare the forester with the approved turnaround](Views/Forester-reference-comparison.jpg) · [See the chopping correction](Views/Forester-chop-before-and-after.jpg)
- [Compare the owl with the approved turnaround](Views/Owl-reference-comparison.jpg) · [See the strike and recovery](Views/Owl-native-strike-sequence.jpg)
- [See the load enter the starter FOOD shelf](Views/Starter-food-delivery.jpg) · [Compare the reference transfer timings](Views/Reference-timing.jpg)
- [Inspect the characters from the 4K gameplay camera](Views/Ultra-characters-closeups.jpg) · [Open the full 1× frame](Views/Ultra-contact-1x.jpg) · [Open the full 2× frame](Views/Ultra-haul-2x.jpg)

## Independent review

One reviewer followed the reference footage and game cameras throughout this revision. A second reviewer checked the rig and final art independently. They reopened the sprint for sleeve, boot and stopping defects and the forester for a hidden axe contact. The same reviewer assignment and the owner's 9.5/10 threshold are written into the project instructions for future changes. [Project instructions](../../../HavenlineLevel1/AGENTS.md) · [Reference timeline](Verification/Reference-timeline.md) · [Independent review of all four areas](Verification/Independent-critic/Review.md) · [Character 1 review](Verification/Independent-critic/Character1-gate.json) · [Companion reviews](Verification/Independent-critic/Companion-decisions.json)

Character 1, the forester, the owl and the transfer presentation each independently passed at **9.5/10**. The transfer review covered the FOOD shelf, all three machine hoppers and the staged purchase plots at normal and pinch zoom. Standing directly on a plot can briefly cover part of its title while the price remains legible. The independent rig validator checked 1,168 entries spanning four clips and 50 joints. The packaged critic helper was unavailable, so the reviewer implemented and ran its documented acceptance conditions against the exact asset and runtime evidence. A published forester strike cadence could not be established from the supplied ads. [Character measurements](Verification/Character1-gait-review.md) · [Forester review](Verification/Forester/Review.md) · [Owl source and rig](Verification/Owl/Source-and-rig.json)

A new forester generation cost **15 Meshy credits**. Its painted master is 2048 × 2048. Recovering and rigging the two existing owl models cost zero new credits. The stills were rendered at **2160 × 3840** with Ultra settings on Linux. Physical Fold7 installation, speaker output and sustained device frame rates remain unmeasured. [Render receipt](Verification/Ultra-field-render.json)

## Package and save checks

The APK uses the same package ID and signing certificate as the previous trial. The signed game resources ran in isolated Godot profiles on Linux. Both the original failed delivery and the fixed delivery used synthetic phone controls. The old save was copied before each comparison. [Signed APK](Verification/Android.json) · [Packaged gameplay checks](Verification/Signed-APK-field-smoke.json) · [Meat delivery](Verification/Android-meat-delivery.json) · [Mixed delivery](Verification/Android-mixed-delivery.json) · [Gate crossings](Verification/Android-touch-gates.json) · [Native regression suites](Verification/Native/Native-results.json)

All 35 native suites passed across 36 launches. The settlement suite passed 208 checks across 16 isolated processes, including interrupted payments, workstations, rescue, deliveries and cold resume. [Settlement results](Verification/Completion/Completion-results.json) · [Private APK download verification](Verification/Private-download.json)
