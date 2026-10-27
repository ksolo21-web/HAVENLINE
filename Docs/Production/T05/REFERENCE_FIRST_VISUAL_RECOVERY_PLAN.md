# T05 Cooker — Reference-First Visual Recovery Plan
Date: 2026-10-27
Status: ACTIVE TRIAL — NOT VISUAL APPROVAL
Scope: T05 cooker, source reference `18567.png`; no shipping asset promotion

## Objective
Reconstruct the cooker so that its actual rendered silhouette, component proportions, material identity, and distinctive details match the approved source render. The existing R07 candidate is an unapproved baseline (previous internal visual score 5.5/10), not a style authority.

## Temporary trial and permanence decision
This is a focused trial, not a permanent architecture change yet. Adopt as the permanent game-wide asset production standard only after the cooker demonstrates independently reviewed, source-image-bound fidelity gains with reproducible renders and no loss of Godot functionality. If successful, encode it as a required upstream stage for all future assets. Keep global pipeline PR #103 separate.

## Source-of-truth and comparison contract
1. Pin exact source image `18567.png` by file hash, original dimensions, origin, and license/owner authorization. If source bytes cannot be obtained, mark all visual comparisons BLOCKED, not PASS.
2. Preserve immutable baseline R07 editable .blend, GLB, and seven 4K isolated Godot renders. Never treat the baseline render as the reference.
3. Record source camera approximation and matching render camera, framing, crop, lighting, and visible surfaces. Report uncertain/occluded geometry as uncertain, not proven.
4. Render matched views after every modeling change. Save source SHA, candidate SHA, render SHA, camera settings, and side-by-side annotated comparisons.
5. Separate **geometry fidelity**, **material fidelity**, **lighting/camera mismatch**, and **unobservable details**. Never hide a geometry defect by camera tricks, overlays, textures, or postprocessing.
6. Use visual assessment of source image vs rendered image. Automated pixel difference is only a supporting diagnostic where alignment and lighting are controlled; it is not an independent critic.

## First correction queue (highest visual impact first)
| Priority | Component | Known issue | Required evidence |
|---|---|---|---|
| P0 | Roof / snow silhouette | Wrong snow scallops, thickness, overhang and edge profile | Source-matched silhouette overlay and annotated 4K view |
| P0 | Saw/metal cooker enclosure | Arch, housing shape and proportions inconsistent | Reference crop, orthographic geometry check, matched 4K view |
| P0 | Food | Item shape, proportions, placement and distinct colors inaccurate | Reference crop, mesh silhouette and matched render |
| P1 | Base | Construction too simplified / proportions incorrect | Source crop, dimensional proxy and matched render |
| P1 | Smoke, supports, trim | Missing or inaccurate distinct details | Annotated source crop and close-up comparison |
| P2 | Material surface polish | Wood, snow, metal, food roughness and normal details | Geometry-approved material comparison under matched lighting |

## Milestones and acceptance
- **R0 — Reference lock:** Verify original source image bytes and authority; record hash and a complete source-region map. Without this, visual claims are provisional.
- **R1 — Silhouette:** Correct roof, housing, food and base shapes. Compare at original camera; no material bake required.
- **R2 — Appearance:** Correct authored materials, colors, snow and distinctive details; retain original nine shader identities unless source comparison justifies change.
- **R3 — Independent visual acceptance:** Reviewer compares exact source vs actual render; requires 10/10 on reference fidelity and visual language, all other mandatory axes >9, no unresolved reference-visible defects. Never fabricate reviewer identity or scores.
- **R4 — Production integration:** Only after R3, run PBR bake, source-preserving UV and normal/AO checks, seven-angle shipping-scene views, actual physical Android sustained 60 FPS and owner/integration-owner signoffs.
- **Permanent adoption:** After R3/R4 pass on the cooker and repeatability is demonstrated, promote this reference-first review contract to the global asset workflow; do not merge draft T05 or global pipeline PRs prematurely.

## Next authorized execution
Retrieve the exact original `18567.png` and compare against the latest R18 source. Produce a crop-by-crop discrepancy register and matched-angle render evidence before making new geometry. Prioritize roof and metal enclosure. Preserve original candidate files, make isolated revisions only, and report genuine improvements and remaining mismatches without unearned scores.

## Current blockers
- Exact source image bytes and latest editable R18 source must be verified together before claiming new fidelity gains.
- No independently accepted reference-match review.
- R07 material-preserving nine-slot baker remains blocked by degenerate/reused source UVs; this is downstream of visual reconstruction.
- No real shipping-scene/Android approval.
