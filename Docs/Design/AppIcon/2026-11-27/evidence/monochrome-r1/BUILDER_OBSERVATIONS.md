# Optional monochrome candidate mechanical evidence

Builder: `/root/icon_source_audit`. Independent reviewer: `/root/icon_critic`.
The candidate remains unselected pending the independent verdict.

The original `sources/monochrome-r1.png` is unchanged. It was uniformly
resized from1254×1254 to257×257 and placed at(88,86) on a transparent432×432
canvas. The entire source canvas fits; no alpha cleanup, thresholding,
creative redraw or source color edit was performed. Preview tinting uses
the output alpha only and does not modify the delivered candidate.

All alpha>=2 pixels fit within radius129.5473px, leaving more than2px before
the132px safe-circle boundary. Four alpha=1 pixels extend beyond132px; the
maximum nonzero-alpha radius is136.6547px. This faint haze is retained and
reported rather than erased or counted as essential content. Exact metrics
and commands are in `adaptive-export-metrics.json` and `commands.txt`.

The raw transparent viewer initially suggested possible noisy holes and
strays. That concern was **not reproduced in the actual output composites**.
The builder inspected `native-themed-dark.png`, `native-themed-warm.png`
and `safe-circle-explanation.png`; the tinted alpha shapes are clean and
the full wordmark remains inside both launcher masks. The snow-hearth/flame
identity remains visible; text is very small at48px and32px.

Themed samples are authored color simulations using the actual delivered
alpha, with a72dp central viewport from108dp layers. No actual device or
launcher run is claimed. Source/export identities and reproduction commands
are retained in `themed-preview-metrics.json` and `themed-commands.txt`.
