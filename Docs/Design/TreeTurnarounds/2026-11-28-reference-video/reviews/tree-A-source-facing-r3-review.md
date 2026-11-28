# Reference A — source-facing anchor r3 retest and checkpoint

**Verdict: the visible gate still fails. Stop the image-generation offset retry loop.** R3 scores **9.4/10** for this single visible face, with **9 of 10 mandatory checks passed**. The9.9 target is unchanged. No version is approved or selected, and the task is not complete.

## Actual reviewed output

[tree-A-source-facing-r3.png](../candidates/tree-A-source-facing-r3.png), SHA256 `b0ee9f0feb92b8a794a08718346fe3e24233f059c03a091e6d9036a3fd98a2f5`, native **1254 × 1254 RGB**.

I inspected the actual full output and the [A61/r1/r3 comparison with identical registration](tree-A-source-facing-r3-evidence/a61-r1-r3-alignment-comparison.png). The uniform scale and translation are exactly those used in the r2 review; no canopy is separately moved to fit. [Evidence transforms and hashes](tree-A-source-facing-r3-evidence/EVIDENCE_MANIFEST.json) are saved. All earlier reports remain intact.

## Open visible defect

**A-SF-01 remains open.** R3 returns from r2’s excessive left shift to a nearly centered apex. In source-space registration, its apex is approximatelyx115–116, close to r1, while A61’s apex is nearx95. The upper-cap body and middle contour sit slightly farther right than r1, so r3 is not the best anchor.

The source-specific cuts, tier proportions, blue surface treatment, relative outline width and short trunk remain useful. This failure concerns visible projected placement and is larger than the source’s pixel uncertainty. It is separate from the permanently unverified hidden-geometry question.

## Best retained drafts — both unapproved

| Purpose | Retain | Scoped fidelity | Open issue |
|---|---|---:|---|
| Single source-facing anchor | [Source-facing r1](../candidates/tree-A-source-facing-r1.png) |9.6/10|A61 upper-cap/apex left offset is still missing.|
| Eight-view reconstruction draft | [Eight-view r3](../candidates/tree-A-360-r3.png) |9.5/10|Inherited convex middle hems remain; common-mesh consistency and unseen source geometry are unverified.|

“Best retained” means useful review history, **not art selection or acceptance**. The scores have different scopes and do not combine into a task pass.

## Required change of method

Do not spend another nearly identical request alternating the crown left and right. The next useful work is a **controllable construction aligned to the original A61 pixels**: editable contours or native geometry, with a fixed source-camera overlay. Retained r1 can help preserve identity, but the original source remains authoritative.

First fix the visible silhouette, tier placement and cuts. Independently review that actual face at9.9 or above with every mandatory check passed. Then render the eight views from one controlled asset and inspect continuity. A native mesh is the suitable path when the deliverable must demonstrate that the views belong to one object.

Unobserved surfaces remain reconstructed unless original asset evidence becomes available. No hidden-angle, common-mesh, turnaround, native/runtime or owner-selection approval is granted here. The saved checkpoint records this dependency order and leaves the task open.
