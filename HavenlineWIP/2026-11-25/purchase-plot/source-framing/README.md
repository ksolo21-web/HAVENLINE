# Level 1 purchase plot: detached source-framing verdict

**Hold RC2. Do not promote a camera-only RC2 variant based on symbol extents.**
This is a ray/triangle screening result, not a fresh rendered frame, dynamic
approach run, mobile measure, art score, or playable integration.

## Revision custody

- Playable baseline `11c14a1c41971067c7dc97db69375f720a408f68`: installs
  `ExactStudioV5_PresentationOnly` using `install_exact()`; it does not
  contain the V6 SVG or `construction_plot_ground.gd`. It uses existing
  `.72` 3D interaction and the yaw `atan2(7,11)`.
- Exact SVG comes from detached V6 at
  `83efcd4e5e5eead175c9addc7ad6f5a8d4848978`, historically .80 m wide;
  RC2 uses byte-identical SVG on a 1.40 m visual square. The terrain generators,
  layout, and hero locomotion source are byte-identical V6 vs 11c. This does
  not say the different preview source is interchangeable or approved.
- RC2 witness manifest seal:
  `512c9a4d3e6d861bccb0a86681b6e853ae68256d4ab7a169b462ed0f09dec9f2`.
  Exact SVG SHA256
  `b59289ae5772fb85855823a3c7daaea78f1846b97e2964340ef9ecfe72eb4476`.
  Prior native approach tracking and same-11c native posed triangles
  are pinned in the sealed input evidence and recorded by SHA256 in result.

## What was checked

Independently sample exact SVG wood and digit alpha (threshold 128; every
other row/column of a 256² isolated SVG raster). Map UV samples to exact
terrain port with the existing 9 mm lift and unchanged plot center. Rebase
previously captured 96,001-triangle CPU-skinned Character 1 idle snapshots
at the logged V6 approach feet and facing. The three captured snapshots are
at the same 0.24136 s animation phase; normalized to the same heading, they
are not three independent animation phases. This is a pose counterfactual,
not a native merged V6-on-11c route. For each parallel orthographic ray,
test actual projected triangle intersection ahead of the plotted sample.
Depth cutoff is 10 nm; same-strength result across the heading-normalized
controls. No extra screenshots or owner/reference source asset bytes
included. Input claims only involve scene-authored model geometry, not
render materials, backface policy, anti-aliasing, mip levels, or terrain/other
occluder after the exact mathematical ray model.

| Camera/control | 1.35 m blocked wood/digit | .90 m blocked wood/digit |
| --- | --- | --- |
| V6 .80 m, 40.15° | 0/759 ; 0/433 | 759/759 ; 366/433 |
| RC2 1.40 m, 57.29° | 345/759 ; 0/433 | 759/759 ; 198/433 |
| Aligned 1.40 m, 65.78° | 70/759 ; 0/433 | 759/759 ; 102/433 |
| Aligned 1.40 m, 72.75° | 0/759 ; 0/433 | 759/759 ; 62/433 |
| Aligned 1.40 m, 80.14° | 0/759 ; 0/433 | 515/759 ; 32/433 |
| Extreme 86° overhead, one snapshot control | not sampled | 151/759 ; 44/433 |

Every tested V6/RC2/ordinary angle control had both symbol masks clear at
the 1.60 m witness. .90 m remains the decisive approach failure: the nominal
RC2 digit box can grow while its wood icon stays entirely behind the hero
in the model. More overhead sampled angles help only partly and materially
alter reference framing; no complete angle sweep or continuous-time result
is claimed. Reproduce from the existing sealed local evidence siblings:

```sh
python3 measure.py > rebuilt.json
cmp rebuilt.json result.json
sha256sum -c SHA256SUMS
```

## Why not a phone pan or zoom fix

Let S be the pad sample, O the spatial camera origin, n the constant camera
direction, R/U the horizontal/vertical axes and k the orthographic scale.
Camera-ray line of sight from this sample is S + t*n. A lateral camera pan,
normalized offset, or size change at the same camera basis only changes its
screen coordinates (k dot(S−O,R), k dot(S−O,U)); it changes neither this
line nor which hero triangle lies on it ahead of S, assuming valid clipping.
This applies regardless of crop or letterbox; it cannot expose a blocked
sample. Change in follow position with no look-at basis change is still a
pan. A larger on-screen box is not evidence of a desirable or readable
outcome. Aspect/runtime behavior on the actual handset is still unverified.

## Next focused acceptance decision

Capture the actual V5-equipped 11c opening first if a graphical runner is
admitted; it is the source people actually play. If the replacement must
improve the ordinary south approach without changing the plot/hero or the
payment radius, the measured result rules out pan/zoom-only and those
sampled fixed-yaw pitch/footprint variants. Ask before trying a localized
occlusion/read-window presentation exception (exact SVG intact; no HUD
duplicate, movement nudge, grace-window charge change, or hero rig edit).
An already known oblique route can serve as a positive render control, not
a substitute for direct south or fresh spawn. After authorization, test
the normal uninterrupted approach, failed funding and one 3-wood commit,
hide once, both gates and fresh restart, then actual effective landscape
phone display. None of those dynamic/visual checks was run in this work.
