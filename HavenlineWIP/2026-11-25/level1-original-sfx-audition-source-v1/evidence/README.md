# Havenline Level 1: original pickup and hearth-earned auditions

Two independent 48 kHz, 16-bit mono PCM WAVs, generated locally using deterministic original oscillators and seeded filtered noise in `render.py`. No sampled/external/reference audio, synth packages, or presets. Combined audition is a convenience sequence, not a third cue, game recording, or final mix.

| File | Designed sound | Seconds | Peak dBFS | RMS dBFS | RMS after 250–4000 Hz filter |
|---|---|---:|---:|---:|---:|
| Wood-Pickup.wav | Two quiet, dry wooden clicks: brief inharmonic strike and softer low knock/rustle | 0.186 | -10.17 | -24.74 | -25.08 |
| Furnace-Earned.wav | Mechanical seat with three ascending warm, lightly overtone-rich tones | 0.684 | -6.38 | -22.63 | -23.44 |
| Havenline-Level-1-SFX-Audition.wav | Three pickups spaced .32 seconds apart, then one earned cue | 2.800 | -6.38 | -26.98 | -27.63 |

`python3 render.py` rebuilds all files, and `sha256sum -c SHA256SUMS` verifies them. Body/detail intentionally live mainly inside a phone-audible band: the mono bandpass is a diagnostic, not a phone-speaker simulation or quality check. File decode and filter completed without errors. Built onset/outro envelopes avoid hard cuts; no clipping. Audio playback could not be auditioned by ear in this environment: audio access was attempted, but audio input was unavailable. Need headphone / device-speaker listening and mix review, not a quality pass.

Keep these bound to the verified wood-pickup commit and first earned furnace receipt only, not a swing, hit, resource transfer, pad hover, repeated receipt or reload. No generated music, installed changes, assets approved, or actual gameplay playback.
