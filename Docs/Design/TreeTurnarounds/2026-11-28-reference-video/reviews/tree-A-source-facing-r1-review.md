# Reference A — source-facing anchor r1 review

**Verdict: revise one projected alignment issue. Visible-face fidelity: 9.6/10; 9 of 10 mandatory checks pass.** The source-first reconstruction solves the stalled generic rim problem, but is still below the 9.9 target. It is unselected and unapproved.

## Exact artifact and evidence

[tree-A-source-facing-r1.png](../candidates/tree-A-source-facing-r1.png), SHA256 `ef1e827596e4df677f4346d87341b6dd659cd0096e543de7377374a5672cc32d`, native **1254 × 1254 RGB**.

I inspected the full anchor, native upper/middle-rim closeups, and an actual uniformly scaled comparison with the original A61/A52 pixels. The comparison aligns tip-to-trunk display height without perspective calibration. It does not replace or modify any original file.

- [Source-scale comparison](tree-A-source-facing-r1-evidence/source-scale-comparison.png)
- [Upper-rim native crop](tree-A-source-facing-r1-evidence/upper-rim.png)
- [Middle-rim native crop](tree-A-source-facing-r1-evidence/middle-rim.png)
- [Evidence transforms, dimensions and hashes](tree-A-source-facing-r1-evidence/EVIDENCE_MANIFEST.json)

## What the new approach solved

The anchor now has source-specific unequal plate ends, deep middle cuts and small side incisions. It no longer relies on the old sheet’s generic rounded two-lobe fan construction. The three tiers, relative crown widths, short brown trunk and blue shading are close in the matched-height comparison.

The contour looks bold when the1254-pixel image is viewed large, but **its relative width is acceptable at the source’s display scale**. Do not thin it simply because this image is larger. Preserve the current material and useful edge/cut detail.

This finding applies to the new visible face. It does not retroactively approve the old sheet’s180°/225° views or establish hidden-side geometry.

## One remaining visible mismatch

**A-SF-01 — the anchor recenters A61’s upper crown and apex.** In the original A61 face, the apex sits clearly left of the trunk/lower skirt. In the anchor it is much closer to the trunk centerline.

Approximate manual source-space positions give a left offset of about **20–24 source pixels in A61**, versus **4–5 source-equivalent pixels in the anchor** after uniform height matching. The upper-cap body itself is roughly12 source-equivalent pixels too far right. These are image-space guides with several pixels of uncertainty, not game dimensions or calibrated geometry; they refine the earlier rough estimate.

**Focused correction:** hold the lower skirt and trunk fixed, retain tier heights, cuts, shading and contour, and match A61’s upper-cap placement farther left. The apex needs a further leftward bias relative to that cap body. Follow the original pixels rather than enforcing a numeric translation. Do not blanket-shift the middle tier on the less certain overlap evidence. A52 corroborates the design but shows another projection; averaging its alignment into A61 weakens this particular source-facing match.

The footage does not prove whether that offset arises from geometry, camera or azimuth. The review asks for the visible A61 projection, not an invented canonical bend.

## Next gate

Make one localized alignment repair on this stronger anchor and retest it before eight-view expansion. No new broad material or rim redesign is needed. This is a single visible-face review only: no hidden-angle, common-mesh, turnaround, native/runtime or owner-selection approval is included. Exact original geometry remains unverified.
