# Reference A tree — independent r1 visual review

**Verdict: REVISE. Visible-source fidelity: 8.8/10. Static cross-view coherence: 9.3/10.** The reference-sensitive target is 9.9 with every mandatory check passed. This candidate passes 10 of 12 checks; two visible-fidelity findings remain open. It is unselected and unapproved.

## Exact reviewed artifact and coverage

- Candidate: [tree-A-360-r1.png](../candidates/tree-A-360-r1.png).
- SHA256: `4b5f0959702dd7fe41367925157b25df4780756fda9085ffe2c51754eb1d55af`.
- Native size: **1536 × 1024 pixels**, RGB. This is not a 4K image.
- Inspected the complete sheet, all eight views at 0°, 45°, 90°, 135°, 180°, 225°, 270° and 315°, and their original-pixel closeups.
- Compared four actual source crops: [A61 clear shoreline tree](../source-a-audit/crops/A61-shoreline-three-tier.png), [A52 pointed tree](../source-a-audit/crops/A52-background-pointed-three-tier.png), [A24 foreground](../source-a-audit/crops/A24-foreground-round-perspective.png) and [A24 smaller tree](../source-a-audit/crops/A24-smaller-three-tier.png).
- Evidence: [first four views](tree-A-r1-evidence/angles-row-1.png), [last four views](tree-A-r1-evidence/angles-row-2.png), [exact crop manifest](tree-A-r1-evidence/CROP_EVIDENCE.json). Source and candidate bytes were not changed.

## What holds up

All eight drawings retain exactly three overlapping icy-blue tiers, a pointed cap and a short red-brown trunk. They use the broader cut-tab family associated with Reference A. They do not replace it with green needles, a round bush or the narrow-incision family seen in Reference B. Tips, skirts and trunks are visible; labels and spacing are clear. The footer calls the sheet a reconstruction.

Scale, tier count, trunk proportions and overall identity remain plausible across the eight views. I did not establish a conclusive impossible geometry jump. That visual coherence does not prove these drawings came from a single rotating mesh.

## Required focused fixes

| Finding | Visible evidence | Repair |
|---|---|---|
| **F01 — rim geometry** | Several hems, particularly the 180°/225° middle rims and lower skirts, are regularized into rounded fan/scallop arcs. A61, A52 and the closer A24 source show flatter, angular polygonal plate ends with more irregular lengths and cuts. | Use A61 as the clear visible-face primary and A24 for edge detail. Match the flat plate ends and uneven cut pattern before extending the design around hidden sides. Keep the established three-tier family. |
| **F02 — surface and contour treatment** | The candidate uses softer bulging gradients and a highly continuous dark navy outline. Source A has more restrained planar/faceted changes and a thinner, less uniformly emphasized contour. | Flatten the material treatment into broad restrained planes and use thin source-like contour edges. Avoid a polished, plump illustration finish. |

These findings are about the actual visible source match, not whether the sheet is attractive. The family is recognizable, but a recognizable reconstruction is below the requested fidelity target.

## Limits and claims to avoid

Overall width alone is not a proven defect: the A24 trees are seen from a steeper camera than A61/A52. A source camera change can substantially alter the apparent proportions, so no exact width-ratio conclusion is used here.

The footage does not show every hidden face at every azimuth. Rear and intermediate drawings can be judged for coherent reconstruction, but cannot honestly be certified as a 100% match to unseen original geometry. Compression and limited source pixels also prevent pixel-identical shader certification. Scores above are scoped visual judgments, not percentages of geometric accuracy.

No runtime, source mesh, rig, native camera or owner-selection approval is implied. Do not carry a prior native-tree approval onto this new sheet.

## Next action

Preserve r1 as an unselected iteration. Make one focused r2 using A61 plus the A24 detail evidence, then compare the exact output against all four source crops and all eight views again. Close F01 and F02; keep the existing family, trunk, clean layout and reconstruction disclosure. The scoped pass requires all mandatory checks and at least 9.9 visible-source fidelity. Hidden geometry remains explicitly unverified even if that visible check passes.
