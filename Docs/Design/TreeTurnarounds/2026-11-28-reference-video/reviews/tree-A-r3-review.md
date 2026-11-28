# Reference A tree — independent r3 retest

**Verdict: revise; change the reconstruction method for the remaining rim geometry.** Visible-source fidelity is **9.5/10**, static cross-view coherence **9.4/10**. R3 passes **12 of 13 mandatory checks**, below the required 9.9 with every mandatory check passed. It remains unselected and unapproved.

## Exact artifact and inspection

[tree-A-360-r3.png](../candidates/tree-A-360-r3.png) — SHA256 `f2145a70c13e4660729d8a35c93561e591f7d9f9e765f6e5675dcef29ed23e8f`; native **1536 × 1024 RGB**. I inspected the complete output, all eight native-pixel angle crops, and the original A61/A52/A24 reference pixels. R1 and r2 reports remain unchanged.

| Finding | R3 result |
|---|---|
| **F03 — excessive lower flare** | **Closed for this image-space silhouette check.** The lower crown visibly narrowed. Approximate lower-to-cap width is now 1.45, near A61’s approximately 1.48; the old r2 value was about 1.67. These are manual image diagnostics, not canonical asset dimensions. |
| **F02 — contour and surface treatment** | **Remains closed.** The thinner edge and restrained planar highlights are preserved. No broad material rewrite is requested. |
| **F01 — long convex middle hems** | **Still open; this correction has stalled.** At 180°/225°, the middle rim retains essentially the same broad two-lobe convex silhouette around a central V. R3 narrows it slightly but does not replace it with a materially source-matched uneven straight plate-edge profile. |

## Actual comparison evidence

- [R2 → r3 → original source proportions](tree-A-r3-evidence/r2-r3-source-proportions.png): shows the successful lower-flare correction.
- [R2 → r3 middle-hem closeups with original A24 edge detail](tree-A-r3-evidence/r2-r3-middle-hem-comparison.png): shows why F01 remains open.
- [All top-row angles](tree-A-r3-evidence/angles-row-1.png) and [all bottom-row angles](tree-A-r3-evidence/angles-row-2.png).
- [Crop coordinates and hashes](tree-A-r3-evidence/CROP_EVIDENCE.json); [approximate width retest](tree-A-r3-evidence/MANUAL_SPAN_RETEST.json).

Source A24’s visible edges are divided into more distinct straight runs with angular corner changes. The remaining candidate hems still read as inherited rounded fan lobes. This is an edge-treatment comparison; it does not claim the footage reveals exact hidden-side notch positions.

## Is another similar sheet edit justified?

**The series has made real gains, but the remaining rim correction is stalling.** R2 improved the material/contour and r3 improved proportions. Two focused edits have left the inherited middle-hem construction nearly unchanged. Another nearly identical whole-sheet request is unlikely to be a good use of generation effort.

The next useful step is a **source-first single-tree reconstruction** at the clear A61 visible camera, using A52 and A24 as corroboration. Match the actual unequal plate ends, notch depths and contour changes on that one visible face, while preserving the now-correct general proportions and restrained material. Independently review that source face before extending it to eight views. This changes the method without changing the tree family or lowering the fidelity requirement.

All eight current views remain plausible members of one design family with three tiers, pointed cap and tiny trunk. No conclusive impossible geometry jump was found. Eight drawings do not verify a common mesh or exact rotational topology.

Even a future visible-source pass would not certify 100% of unseen original geometry. No native, runtime, source-shader or owner-selection approval is included. Preserve r1–r3 and their receipts as review history.
