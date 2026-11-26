# Directional shadow trial

A fixed paid-court capture compared the original 4096-pixel atlas and four cascades across 36 m with reduced cascades in an isolated 1280 × 720 software render. The final scene retains the original four cascades.

At the same 36 m distance and atlas resolution, two cascades changed 11.9% of image pixels by more than eight RGB levels at both normal and 2× zoom. One cascade changed 18.0% and 17.5%, respectively. Snow and tree contact patches changed visibly. The reported draw counts and primitive counts stayed equal for all three configurations in each view. Timing samples included a framebuffer readback on a busy software renderer, so a playback speedup was unverified.

Disabling shadow casting only on the ground mesh eliminated one draw and twelve triangles. The mean pixel difference was 0.05/255 at normal zoom and 0.11/255 at 2×. The scene retains the original setting.

[Paired screenshots](Shadow-study.jpg) · [30 m and floor data](Shadow-comparison.json) · [Matched 36 m trial](Shadow-distance.json)
