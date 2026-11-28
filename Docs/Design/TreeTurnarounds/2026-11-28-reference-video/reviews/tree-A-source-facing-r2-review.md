# Reference A — source-facing anchor r2 retest

**Verdict: revise — the alignment correction overshot.** Visible-face fidelity is **9.3/10**, with **9 of 10 mandatory checks passing**. R2 is not ready for eight-view expansion and remains unselected/unapproved.

## Exact reviewed output

[tree-A-source-facing-r2.png](../candidates/tree-A-source-facing-r2.png), SHA256 `ddf172823fc748815563aaab804f04b2d58331a5dfc7f2018add1f80e863c660`, native **1254 × 1254 RGB**. The r1 report is preserved.

I inspected the actual output and a [same-scale A61/r1/r2 comparison](tree-A-source-facing-r2-evidence/a61-r1-r2-alignment-comparison.png). Both candidates receive exactly the same uniform scale and translation, preserving source height/trunk registration; individual tiers are not separately aligned. [Evidence details](tree-A-source-facing-r2-evidence/EVIDENCE_MANIFEST.json) record the transforms and hashes.

## Concrete remaining error

The upper cap moved roughly110 native pixels left, and the middle moved roughly80—substantially farther than the prompt requested. The lower skirt also drifted left while the trunk remained in place.

At normalized source scale, A61’s apex is approximately **x95**. R1 projects near **x116**; r2 near **x84**. R2’s upper-cap body and middle contour also sit roughly **17–22 source pixels too far left**. These are approximate manual image coordinates, not canonical dimensions, but the overshoot is plainly visible and materially larger than source blur.

**Bounded correction from r2:** bring the upper-cap body right roughly60–70 native pixels, keeping its apex about20–30 pixels farther left relative to that body than a rigid translation would. Return the middle toward r1, roughly50–65 pixels right, and preserve/restore r1’s lower-skirt/trunk registration. Judge the final projection against A61, using these amounts only as coarse brackets.

The source-specific cuts, three-tier identity, material, relative contour width and short trunk remain sound. Another broad style or rim redesign would discard useful progress.

## Iteration limit and next action

This is a visible placement error, not a demand to certify unknowable hidden geometry. One bounded alignment repair is justified. Do not proceed to a turnaround from the overshot anchor.

If another localized edit again disregards the placement constraint, stop alternating approximate left/right requests. Retain the closer draft as unapproved and use a more controllable source-overlay or native construction method before expanding to eight views. The next review should use the same source/trunk registration so improvement can be observed directly.

This review covers one visible face only. It does not approve hidden surfaces, a common mesh, rotation consistency, native/runtime behavior or owner selection. No original files were changed.
