# Havenline Level 1 — first cue-balance A/B test

An offline mix of exactly the previously made music, wood-pickup and hearth-earned sketches. A and B use the same sources, sample-aligned event schedule, rendering settings and SFX gains. The diagnostic has separate Music, SFX and Ambience inputs; Ambience is silent because there is no accepted ambience recording yet. No new sounds or game settings are included.

- **A (0.00–4.25s):** unducked Music, four wood pickups and one hearth confirmation.
- **B (4.75–9.00s):** identical cues and gains; Music alone is lowered by up to 6 dB while a cue fires, with a shaped transition. There's no duck applied to ambience or SFX. This offline preview has 25 ms lookahead; a real event-driven mixer would start on the actual accepted event, not preplay a trigger.
- After 250–4000 Hz filtering, SFX is **1.28–6.12 dB above music** in A's pickup windows and **7.26–12.09 dB** in B. The hearth window increases from **9.40 to 15.39 dB**. A's quietest-margin pickup is at 1.11s, where a scored note overlaps the cue. This is energy, not a listening judgment.
- With both available buses boosted 20% and three pickups near-overlapping 15 ms apart while other pickups and the hearth keep their place in the cue sequence, peak sample level remains **0.64915** of full-scale in A and **0.59012** in B. Both leave more than 20% sample-peak headroom under that fixture. Real dense gameplay, dynamic ambience, true peak, and latency remain unmeasured.

**First listening comparison:** test at fixed, ordinary phone volume and listen for the third pickup in A, exactly what the duck helps in B, and whether frequent pickups make the music audibly dip and recover. Once real ambience is ready, repeat with each of the three controls independently, a dense transfer, cold reload and actual game speakers. B is a useful comparison, not an installed mix or recommendation to enable audible pumping. This environment does not support subjective audio listening; technical decode passed. The playable build was not changed.

The 432,044-byte PCM WAV is a nine-second local audition. Rebuild with `python3 mix.py` and the SHA-pinned prior assets in sibling folders, then `sha256sum -c SHA256SUMS`. Technical results are in `measurements.json`.
