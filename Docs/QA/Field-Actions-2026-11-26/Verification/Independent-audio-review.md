# Native audio evidence

**Technical event audibility scored 9.5/10.** I matched the authored sounds against the recorded Godot master mix. Nineteen of 20 measured onsets met the stated discrimination test: a match within 0.12 s of the gameplay cue and at least twice the 95th-percentile correlation from other time windows. All 20 matched within 0.10 s. This score describes recoverable event identity in these recordings. This review did not audition the mix by ear or measure a physical Fold speaker.

| Action | Matched master times | What the recording supports |
|---|---|---|
| Pack howl | 2.326 s | Present in the wildlife mix, with similarity 5.6 times the off-window baseline. |
| Owl dive and hit | 2.976 s, 3.162 s | Separate wing and impact cues 186 ms apart. The authored hit remains distinguishable amid several competing sounds. |
| Wolf brace and lunge | 4.555/4.926 s, 5.484/5.762 s | Each lunge has a preceding brace, and both lunges stand clear in the measured mix. |
| Wood and stone machinery | Saw 1.397/2.790 s; drill 2.140/3.440 s | Both motor cues appeared independently at both onsets. The second saw sits roughly 13 dB below the surrounding mix when averaged over 380 ms. |
| Machine outputs | Plank 2.790/4.090 s; block 3.440/4.833 s | Both material signatures are present. The first block discharge coincides with the second drill onset and is the one cue below the 2× separation criterion. |
| Cooker, meal and payment | Griddle 2.790/4.369 s; roast 4.369/5.855 s; cash 6.505 s | Distinct matches even where production cycles overlap. |

The two source FLACs were captured at 44.1 kHz, stereo, with zero reported dropped frames and zero clipped samples. They contain 16.254 s of camp audio and 8.080 s of wildlife audio. Their transfer gates, machine actions and combat are real runtime events in a disposable scene where the capture driver positioned the player. The sources and recorded event times are in `../audio`.

I decoded both master recordings and the twelve source WAVs to 12 kHz mono, high-passed at 250 Hz, and measured normalized waveform correlation over the first 380 ms at the three runtime pitch variants. Each result and its off-window comparator is in `Independent-native-audio-fingerprints.json`. The start tolerance covers the native capture buffer interval and logging cadence. This test cannot establish artistic timbre, stereo imaging, speaker response, or parity with the original ad soundtrack.

The final 540 × 1260 encounter movie was also checked after AAC encoding. Its 113-frame gameplay track and 48 kHz stereo track each span 5.65 s. The movie carries both wing sounds and two accepted talon hits, three distinct wolf lunges, and three player damage events on the same timeline. The strongest owl-hit matches occurred at 0.954 s and 4.709 s. Wolf lunge matches occurred at 0.911, 2.106 and 3.909 s. See `Independent-encounter-film-audio.json`.
