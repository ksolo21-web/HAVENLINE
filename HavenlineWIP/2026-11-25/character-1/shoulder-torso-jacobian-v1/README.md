# Left sleeve and pinned torso: local 52-joint DQS feasibility HOLD

This is not a new pose trial, animation, rig/garment edit, export or release. It diagnoses the exact failed whole-arm open sample with zero strict shaft intersections but an actual chest-coat/left upper sleeve crossing. It verifies both independent and author freeze seals, reconstructs both published source-position hashes with the exact owner-source v2 dual-quaternion skin, and correctly distinguishes the anatomical elbow hinge from an arm-axis guess.

## Pin Jacobian and direct collision dependency

Each side has three local shoulder rotation directions around the actual joint (longitudinal, in-plane orthogonal, and bend-plane normal) and one anatomical elbow rotation around the actual elbow's bend-plane normal. Torso, clavicle, bind positions, model/weights, both upper-limb lengths, tool, grip stations, and relative local wrist/digits are frozen. Allowing all three shoulder directions is a superset of restricted shoulder angular ranges; it does not prescribe angles. Under these coordinates, actual point derivatives are evaluated by central dual-quaternion differences at 5, 10 and 20 microradians. These are infinitesimal probes, not angles selected by a pose sweep.

The sensitive chart set is **1,160 left and 1,131 right exact source rows** used in the independently verified chest author's non-arm-dominant torso chart (600,396 indexed faces), not a rasterized appearance region. The central core of 229,322 original indexed rows is unchanged. At the original authored held baseline and rejected tool-clear open reference, the same chart rows give **rank 3 of 4** per side. Every nonzero shoulder velocity moves at least one pinned row; the single elbow column is exactly zero (the stored pins have no positive elbow-subtree weights). Splitting each source-sorted block into independent alternating half-witnesses preserves the rank, as do all three step sizes. At the open point:
- Left raw stacked shoulder singular values are roughly 0.254305, 0.228137, 0.044032 m/rad; corresponding weakest RMS per source point is 1.293 mm/rad (condition 5.78).
- Right are 0.265071, 0.248826, 0.047078 m/rad; weakest RMS 1.400 mm/rad (condition 5.63).
- Largest cross-step matrix-entry differences are under 5×10⁻¹¹ m/rad. This is not a tiny or rank-threshold-unstable shoulder constraint.

Original triangle **556546** is fixed spine/chest/clavicle skin; **674738** is entirely left upper arm. Neither triangle depends on the elbow or its descendants at all; the pure sleeve triangle has a nonzero analytically verified derivative under a *free* shoulder. The separately archived signed-plane proof reports the 2.761 mm strict intersection line in the open sample, not a penetration depth. Therefore the allowed nonzero **elbow-only null direction cannot separate this pair**. This holds under the tested fixed-chart coordinate families, locally around these two references; it does not prove absence of distant workarounds or of compensated/clavicle approaches outside this task. This did not recalibrate tool clearance or model a physical swing.

## Exact scope of a future decision

Do not relax the entire torso or redo angle sweeps. A different well-defined rig/pose formulation would require explicitly scoping the side transition: for the measured left obstacle, the 1,160 sensitive **left outer chart rows** have bind X=181.871–215.832 mm with separately recorded Y/Z bounds. The measured right counterpart is 1,131, abs X=181.742–214.288 mm. These are exact chart-contributor sets for the tested motion, not a claim that all those vertices must move for every possible correction. The named fixed chest triangle is a distinct source surface and is not within the left upper-arm mask. A real future proposal must either define a bounded allowed transition/compensating rig while protecting the actual coat and silhouette, or obtain specific consent for a narrow, physically justified adjustment of that side's existing shoulder skin or chart constraint. No permission to move the central core, alter weights/material broadly, or sacrifice the named chest/arm geometry is inferred. A new stage must be reviewed for both original source custody and actual independent fit before proceeding to tool reacquisition/contact.

## Reproduce only in read-only source workspace
```sh
bash run.sh /path/to/exact/held_owner.npz > replay.json
cmp replay.json result.json
sha256sum -c SHA256SUMS
```
