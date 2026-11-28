# Reference A tree — independent r2 retest

**Verdict: REVISE. Visible-source fidelity 9.2/10; static cross-view coherence 9.4/10.** R2 is closer to the source, but 11 of 13 mandatory checks pass. The reference-sensitive target remains 9.9 with every mandatory check passed. No selection or approval is granted.

## Exact output inspected

[tree-A-360-r2.png](../candidates/tree-A-360-r2.png), SHA256 `f6764a85ee6e82e6c7339ed6efbb8966b62f02fe37a8b587784ec26b972dd506`, native **1536 × 1024 RGB**. I inspected the full sheet and all eight native-pixel angle crops against A61, A52 and both A24 references. The r1 report remains unchanged.

- [Direct source comparison](tree-A-r2-evidence/visible-source-comparison.png)
- [Angles 0°–135°](tree-A-r2-evidence/angles-row-1.png)
- [Angles 180°–315°](tree-A-r2-evidence/angles-row-2.png)
- [Original-pixel crop manifest](tree-A-r2-evidence/CROP_EVIDENCE.json)

## Retest findings

| Finding | Status | Actual result / next correction |
|---|---|---|
| F02: heavy outline and soft material | **Closed for this static visual scope** | The contour is visibly lighter/thinner and broad planar highlights are clearer. Keep these improvements; another general style rewrite is unnecessary. This is not certification of the original shader. |
| F01: rounded plate hems | **Improved, still open** | Several tabs gained corners, but at 180° and 225° the two main middle hems still sweep in long convex arcs around the central V. Break those arcs into unequal straight plate-edge segments with crisp joins, carrying one consistent arrangement through adjacent views. This matches the visible source edge treatment without pretending to know unseen notch positions. |
| F03: relative crown widths | **Open** | The 0° lower skirt flares too far beyond the upper cap compared with A61/A52. Match those source proportions while preserving the cap height, three-tier family and short trunk. |

The width observation is specific to **lower-skirt width relative to upper-cap width**, not overall tree width/height. Approximate manual source-pixel spans are 149 px cap / 249 px lower skirt for r2 (ratio about 1.67), and 124 px / 183 px for A61 (about 1.48). Boundaries have roughly ±3 px uncertainty, and there is no camera calibration. These are diagnostic image measurements, not asset dimensions. The [measurement record](tree-A-r2-evidence/MANUAL_SPAN_DIAGNOSTIC.json) preserves that distinction.

For a focused repair, start by drawing the lower flare inward roughly 10–12%, with only a mild middle-tier adjustment, then judge directly against A61. Do not reshape the upper cap or change the tree family to satisfy a number. A24 has a steeper camera and does not support a total width/height comparison.

## What remains sound and what remains unknown

All eight views retain the blue three-tier identity, pointed cap, short brown trunk, clear labels and complete framing. Their static scale and design family remain plausible. No conclusive impossible cross-view geometry jump was found, but a single common 3D mesh is not established by eight drawings.

The footage cannot certify unseen rear geometry at every azimuth. A future visible-fidelity pass would still mean a source-grounded reconstruction, not a literal 100% original-asset recovery. The sheet is 1536 × 1024, not 4K; no native/runtime or owner-selection approval is included.

**Next action:** preserve r1 and r2, make the two localized geometric corrections, then retest the exact resulting file against every open finding and all eight views. Do not reopen the resolved broad material treatment without new evidence.
