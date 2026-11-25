# Level 1 outdoor air and earned hearth — two independent ambience sketches

Original deterministic oscillator/noise designs, no recordings or reference samples. `recipe.json` edits duration/seed/bands/levels and preview timing; `render.py` rebuilds locally using NumPy 2.3.5 and FFmpeg. All three mono 16 kHz PCM auditions together are 672,132 bytes. Six-second cycles are for evaluating direction, not a final seamless-in-play ambience length.

| File | Technical evidence |
| --- | --- |
| Havenline-Winter-Air-Loop.wav | 6 s, quiet smooth-air design, −19.00 dBFS peak / −32.47 RMS; 3 decoded cycles byte-identical, PCM seam step 98 vs neighboring maximum 578 |
| Havenline-Earned-Hearth-Crackle-Loop.wav | 6 s, muted ember/soft crackle design, −17.00 peak / −34.80 RMS; 3 decoded cycles byte-identical, PCM seam step 116 vs neighboring maximum 711 |
| Havenline-Ambience-Fresh-Earned-Restore-Test.wav | 9 s, −19.25 dBFS sample peak. Air-only through 2.0 s, hearth fades in over .7 s as if newly earned and nearby. Silence .5 s separates sessions; at 5.25 s both beds fade up as if restored paid and nearby. No build confirmation audio is included. |

The two unattenuated beds' conservative combined sample-peak ceiling is 0.25346 full scale. Actual decoder output matches written PCM, and the pre-earned hearth samples and separation gap are all zero. Source loop repetition, low peaks and separation do not certify subjective sound, app audio focus behavior, engine looping/seams, collisions or a complete mix. Audio input capability was unavailable for subjective review. Listen through several repeats on a physical phone, including with music and repeated high-priority SFX so ambience never masks them.

**Separate runtime dependencies, not implemented:** outdoor air can follow one loaded eligible Level 1 session and owner settings; no added weather state. Hearth additionally requires actual published paid camp/hearth and a spatial near/far/fade policy verified against the active scene. A real cold restoration reads already-paid state; do not call or play the initial build one-shot at hydration or on approach. Failed saves, unearned state and blocked/rejected purchases keep hearth absent. No recipes, actors, music or runtime changes. This bench demonstrates layer separation and envelopes without asserting authority from simulated time markers.
