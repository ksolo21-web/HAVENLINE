# Original-owner C1 bilateral grip material intake: HOLD for authoring

This is the detached **52-joint owner source**, unchanged original 512-facet axe, and identical previously frozen chest-held frame. No PR108 mesh/rig, new neutral pose, skin displacement, boot/body/outfit edits, DCC, runtime, gameplay or network activity. Inputs are exact hashes in result. Direct original GLB decode matches all 425,291 bind rows and all 727,442 held/bind face indices; texture samples come from the unmodified authored base-color asset. The source is a single indexed material with a texture atlas, so skin influences and pixel samples must not be used as entire anatomical-material labels.

## Right web and cuff custody

The right thumb/index root role transition is exact vertex edge 7002–7333, incident faces 12584 and 12585 with reverse winding and the exact same indexed UV edge. Both endpoint texels are brown. This is a real local joined chart witness, not a complete right web seam. The left has six narrowly qualifying edges. Exact original source triangles, IDs and both sides of the cuff are unchanged.

Neither side has an indexed-edge-only path from its selected role transition to the main preserved cuff branch inside the scoped distal hand region. A separate **read-only** diagnostic adding virtual links only between bit-identical bind AND held positions finds a right route of 115.156 mm to original cuff edge 11329–13517 through **three** distinct UV aliases, and a left route of 87.815 mm to 410914–411192 through **one**. The right atlas jumps reach 0.887 in normalized UV. This is not permission to weld/collapse any alias, call the complete web manifold, or interpolate texture between either chart. The exact indexed route and alias IDs are in the result.

## Palm seat/contact and protected-forearm distinction

The earlier exact finite tangent fixtures are 356.425 mm² right on original facet 124, 366.465 mm² left on original facet 276. They are target geometry, not attached pressure leather. New nine-point deterministic contact-seat support search on each finite target finds real original distal shell by facet-normal line intersections (bounded ±35 mm). All nine left samples find exterior-side source 0.81–3.75 mm away and no inner-side hits in range. Right only yields five exterior-side samples (one near zero) and **four inward-side** samples −0.62 to −0.06 mm; the right seat therefore cannot be treated as an already usable uniformly outward patch. This is signed source correspondence sampled at nine points, not true volumetric penetration depth or a whole-shaft/continuous support guarantee.

Recomputed all 22 prior tool/forearm-weighted pairs with strict bidirectional segment/triangle intersections. Important scope correction: all 22 pairs have every face vertex inside the exact owned distal section beyond the preserved cuff bind plane (31.18–51.38 mm overall, 41.50 mm minimum right). Cuff plane reconstructed from exact traced cuff endpoints (<1e-12m residual); derived side is checked with original nominated distal palm. This demonstrates that "forearm-weighted" does **not** make those particular triangles protected proximal forearm geometry, and a glove-only path is not disproved on that claim. It does not establish whole retained-forearm or coat clearance for any successor, and all 22 still cross in the original pose.

## Stop and exact next construction prerequisite

A usable bilateral attached seat is **not yet established**. The left nine outward samples are suitable correspondence anchors only; right has mixed shell signs plus three UV aliases to the cuff, so merely snapping both palms to the tangent fixture would move a mixed/possibly inappropriate shell sector and risk crossing a protected seam or changing texture custody. Do not author another point-only snap, arbitrary topology weld, alternate tool scale, boot or forearm geometry. Next lawful construction should first close one specifically mapped right seat patch graph: start from inward right source faces 15906/15909, trace both sides into the common local 7002–7333 right web incidence without crossing the intact cuff, and maintain distinct copies at 7699/7754, 8224/8284 and 10268/10274. Establish a shared signed orientation and fixed-boundary interpolation for actual glove skin over facet 124, then test paired left and right finite bearing plus complete retained garment/tool/inter-hand clearance before calling a candidate. Exact input is available; missing item is this connected source/UV-preserving bounded construction, not new owner art, a stock substitute or grounds to broaden scope. No prototype or speculative release included.

## Reproduction

```sh
OPENBLAS_NUM_THREADS=1 python3 intake.py <original-owner.glb> <bind.npz> <held.npz> <frozen-seam.npz> <frozen-chest.json> <original-axe.glb>
```

Requires NumPy, Pillow and SciPy. Reads only. Output must equal result.json; no raw source models, textures, mesh geometry bytes or private paths are packaged.
