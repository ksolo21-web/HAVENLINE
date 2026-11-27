# Adaptive color mechanical evidence

Builder: `/root/icon_source_audit`. Independent reviewer: `/root/icon_critic`.
This is mechanical evidence and builder observation, not independent approval.

The source `sources/named-foreground-r3.png` was uniformly resized from
1254×1254 to 353×353 and placed at (39,44) on a transparent 432×432 canvas.
The whole source canvas fits in the output. No thresholding, background
removal, manual cleanup, color edit or creative redraw was performed.
The explicit background is uniformly opaque RGB (6,22,61), or `#06163d`.

The measured safe circle has radius 132px. Every alpha>=2 output pixel is
inside radius 129.8942px, exceeding the requested 2px safety margin. Every
nonzero-alpha output pixel is inside radius 130.5393px; none is outside the
132px safe circle. Full exact metrics, source identities, commands and
derivation are retained in `adaptive-export-metrics.json` and `commands.txt`.

The builder inspected `native-launcher-dark.png`, `native-launcher-light.png`
and `safe-circle-explanation.png`. The launcher simulation first crops the
central 288px (72dp) viewport from the 432px (108dp) composite, then applies
circle/squircle masks and renders actual 96/64/48/32px samples. This avoids
mistaking the padded full108dp layer for the visible launcher icon.

The warm hearth and complete wordmark remain visible in both shape masks.
Text is small at64px and very small at48px;32px retains the hearth identity.
No clipping was observed. These are representative simulations; no Android
device installation or real launcher certification is claimed.
