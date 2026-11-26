# Havenline Level 1 audio review

Both excerpts are stereo recordings from the Godot 4.7.2 Master bus at 44.1 kHz. The scene was field_opening.tscn. Each run used a disposable profile and normal gameplay event handlers. The capture driver positioned the player at the review locations. The encounter run also launched a seeded pack through the live encounter manager. The game chose the attack, contact, processing, cooking and sale events. FLAC preserves the captured mix. MP3 is provided for playback.

| Recording | What to listen for | Integrated | True peak |
|---|---|---:|---:|
| Camp-workshop-and-counter.mp3, 16.25 s | Saw at 1.39 s, crusher at 2.14 s, distinct plank and stone drops, roast at 4.27 s, player collecting at 5.20 s, paper payment at 6.41 s. Orbit resumes after exiting the camp. | −22.0 LUFS | −8.5 dBTP |
| Owl-and-wolf-encounter.mp3, 8.08 s | Pack arrival at 2.32 s, wingbeats at 2.97 s, confirmed talon contact at 3.16 s, wolf braces at 4.55 and 5.48 s and lunges at 4.83 and 5.76 s. Wood and meat pickups overlap the action. | −20.5 LUFS | −6.3 dBTP |

The production run produced two planks, two stone blocks, two cooked meals and one payment. The encounter started from an archived, earned v4 profile with one prior owl hit, and ended with two. Both sessions reported zero dropped capture frames and zero clipped samples. Their cue timestamps are in Audio-measurements.json.

| Gameplay family | Audible behavior |
|---|---|
| Field, sanctuary, danger | Alfred’s sixteen-beat, 96 BPM field motif runs continuously. Camp and threat use separately arranged, synchronized stems and smoothed gain. A hostile wolf just beyond the fence preserves the camp arrangement while the hero is safe. Wind covers the field. The earned hearth has proximity-based fire. |
| Player movement and tools | Separate footfalls on camp and snow; three variations per surface. Axe and pick equip, orbit sweep, hit and carry Foley are spatialized. |
| Harvesting and materials | Wood and stone have distinct impact, depletion, drop, deposit, spend and regrowth cues. Coal, slate and metal inherit the stone family at 0.84×, 1.08× and 1.19× pitch. Timber and ore machinery have different motor and discharge sounds. |
| Purchases, reveals and gates | Material spend on successful delivery, purchase and construction accents, a delayed reveal at the founding hearth, gate hinge and latch. Later plots revealed by progression use the existing purchase/reveal sequence. |
| Wolves, hero, owl and tower | Pack howl, approach, windup, lunge, accepted hero damage, player fall and reset. Wolf hit, defeat and meat drop. Boss arrival/defeat and tower release/impact have distinct cues. The owl has one recruitment call per successful plot receipt, separate dive wingbeats, and a talon cue only after an accepted hit. |
| Survivor, machines and customers | Survivor rescue has a two-note answer. The worker uses carry, material spend and deposit cues for actual transfers. Saw and drill have independent start and finished-output cues. Cooker has griddle start and a tray-ready cue. Pickup at the output remains tactile. Customers handling payment emit one paper receipt on the successful sale. |
| Progress, focus and master mix | Level completion and transition reuse the established victory/reveal motifs. Important receipts duck the score and have reserved voices. Foreground effects pan along the camera’s screen-right axis and attenuate with distance. Global mute, application focus and scene pause silence the audio output. |

The realtime native regression loaded every variant, measured all 56 canonical cues on the Master bus with music and ambience muted, verified 31 alias/mineral routes, sampled all three audible music states and measured digital silence under global mute. Audio-measurements.json also gives source waveform duration, peak, RMS, channels, digest and sample rate. All five of Alfred’s archived inputs match their original SHA‑256 checksums.

Ten sound files were rendered locally, including a replacement for the prior quiet pack-return shuffle. No paid sound libraries or generation services were used. The score is original to Havenline. Tracking individual incidental customer footfalls and synchronizing every animal paw with Foley are outside the event coverage shown here. This evidence measures the engine mix. Physical Fold speaker response and matching a particular ad’s soundtrack remain unverified.
