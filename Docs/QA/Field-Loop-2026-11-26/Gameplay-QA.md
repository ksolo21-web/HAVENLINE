# Field-loop gameplay verification

[Watch the uninterrupted gameplay recording with sound](Field-Loop.mp4). The scene is `res://field_opening.tscn` at commit `994ace861fbf132c5924bacc320f5608d75d9187`. An empty disposable profile provided the first frame. All movement, harvesting, hunting, pickup, spending and gate crossings came through the running scene. The recorder sent one-finger joystick gestures, a two-finger pinch and presses on the two gate controls.

| Playback time | What to watch |
| ---: | --- |
| 0.8 s | Cut the starter pine |
| 6.1 s | Break the mine with the pickaxe |
| 14.9 s | Wolf encounter and axe contact |
| 21.3 s | Read all three carried stacks |
| 24.40–25.03 s | Watch three wood debits, then the built court and hearth |
| 41.9 s | Three dedicated floor stacks |
| 44.70–45.03 s | Two stone and one meat pay for the three-axe upgrade |

### Functional results

- The starting pine took three true axe contacts. The mine took three pickaxe contacts. The wolf entered attack range, lowered the player's health, took three registered hits and dropped two meat units.
- Wood, stone and meat traveled visibly into separate rack positions. The return trip carried 3 wood, 3 stone and 2 meat. The hearth consumed three wood. The court, furnace and gates appeared once.
- A second harvest restocked the wood route. The three floor plots reached wood 6, stone 3, meat 2. The upgrade consumed two stored stone and one stored meat, and the visible tool count changed from one axe to three. The field uses typed materials as its purchase currency.
- A fresh process reopened the earned save and recovered the court, both active gates, three axes, 6 wood, 1 stone and 1 meat. The rack was empty and both payment receipts remained complete.

| Gate | Direction | Playback | Distance from opening center |
| --- | --- | ---: | ---: |
| South | Outward | 27.61 s | 0.09 m |
| South | Inward | 33.82 s | 0.02 m |
| East | Outward | 48.63 s | 0.02 m |
| East | Inward | 51.81 s | 0.08 m |

Playback starts at the first settled route sample. Payment time ranges use the encoded frames displaying the state changes. Gate times are interpolated from the 60 Hz observations, with a video frame every 1/30 s.

Each crossing was measured where the player path intersected the gate plane with the corresponding gate open. Exterior snow remained visible during the two outward legs.

### Images and sound

[Landscape opening](Gameplay-Stills/Landscape/01-before.png) · [Portrait opening](Gameplay-Stills/Portrait/01-before.png) · [Hunting contact](Gameplay-Stills/Portrait/04-wolf-lunge.png) · [Mixed carried stack](Gameplay-Stills/Landscape/06-loaded.png) · [Partial payment](Gameplay-Stills/Portrait/07a-payment.png) · [Hearth reveal](Gameplay-Stills/Landscape/07c-reveal-rise.png) · [Completed court](Gameplay-Stills/Portrait/07-built.png) · [Three floor plots](Gameplay-Stills/Landscape/08b-stocks-clear.png) · [Gate and exterior snow](Gameplay-Stills/Landscape/10-gate-exterior.png)

[Play the supplementary portrait purchase](Gameplay-Evidence/Diagnostic-Portrait-Hearth-Purchase.mp4) · [Play the wolf defeat and recovery](Gameplay-Evidence/Diagnostic-Wolf-Defeat-Recovery.mp4). Both diagnostics are labeled with the pre-freeze source fingerprints in their accompanying receipts.

The movie contains 1597 native 1280 × 720 samples over 53.233 seconds, encoded at 30 frames/s. The simulation ran at 60 Hz. All landscape and portrait PNGs came from independently played routes using the same following camera. Root readbacks measured 3840 × 2160 or 2160 × 3840 with a 1.0 internal rendering scale. The film includes the validated route’s 1.52× pinch. Independent native still runs reached the full 2× pinch before returning to 1×.

Godot MovieWriter captured the stereo game mix at 48 kHz alongside the video. The playable MP4 contains its AAC encode. The 48 kHz PCM peaks at -5.73 dBFS with 0 silent half-second intervals across the released play segment. The audio receipt lists runtime cue starts and independent waveform matches against the recorded mix. I verified the final chaptered file by full decode. All 1,597 gameplay frames have distinct reduced-resolution luma hashes. The last frame shows the player back inside the paid court. [Frame continuity audit](Gameplay-Evidence/frame-continuity.json) The engine recorded continuously for 29.5 wall-clock minutes on this shared software-rendering worker. Offline llvmpipe capture does not establish phone or tablet frame rate, battery use or thermals.

The owner’s retained clips show the source purchase and upgrade sequences. [Camp purchase](References/Locked-sequences/B-camp-purchase.mp4) · [Axe upgrade](References/Locked-sequences/B-axe-upgrade.mp4) · [Fishing upgrade](References/Locked-sequences/A-fishing-upgrade.mp4) · [Frame provenance](References/Locked-sequences/source-ledger.json)

[Mine contact before and after correction](Gameplay-Evidence/Mine-contact-before-after.jpg) · [Countable meat before and after correction](Gameplay-Evidence/Meat-plot-before-after.jpg) · [Scored gameplay-camera review](Gameplay-Evidence/Native-visual-critique.md)

[Run results](Gameplay-Evidence/route-result.json) · [Typed receipts after fresh-process reload](Gameplay-Evidence/fresh-process-reload.json) · [Audio verification](Gameplay-Evidence/audio-review.json) · [Native camera readbacks](Gameplay-Evidence/source-bound-stills.json) · [Commit and asset hashes](Gameplay-Evidence/source.json)
