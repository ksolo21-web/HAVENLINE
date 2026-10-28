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
- **R3 — Independent visual acceptance:** Reviewer compares the exact original owner source against actual native Godot rendered materials and geometry, not technical build success or Blender previews. **C1 reference fidelity and visual language must be 10.0/10; every other cooker-specific visual axis must be at least 9.5/10**, including food/marbling, snow, steel/wood, roughness, mechanical geometry, cross-view integrity, contacts and smoke. No averages or unresolved defects. Require source-camera alignment evidence, all five real Godot 4K views, all nine authored shader outputs, 6 source reference regions, independently generated raw reviewer output with source/GLB/reviewer/job hashes, and explicit record of visual misses. Review may be human or separate vision model, never the builder. A passed critic is still not user acceptance, shipping-scene proof or physical Android proof.
- **R4 — Production integration:** Only after R3, run PBR bake, source-preserving UV and normal/AO checks, seven-angle shipping-scene views, actual physical Android sustained 60 FPS and owner/integration-owner signoffs.
- **Permanent adoption:** After R3/R4 pass on the cooker and repeatability is demonstrated, promote this reference-first review contract to the global asset workflow; do not merge draft T05 or global pipeline PRs prematurely.

## Next authorized execution
Retrieve the exact original `18567.png` and compare against the latest R18 source. Produce a crop-by-crop discrepancy register and matched-angle render evidence before making new geometry. Prioritize roof and metal enclosure. Preserve original candidate files, make isolated revisions only, and report genuine improvements and remaining mismatches without unearned scores.

## Current blockers
- Exact source image bytes and latest editable R18 source must be verified together before claiming new fidelity gains.
- No independently accepted reference-match review.
- R07 material-preserving nine-slot baker remains blocked by degenerate/reused source UVs; this is downstream of visual reconstruction.
- No real shipping-scene/Android approval.

## Independent R26 critic implementation (2026-10-27)

The C1/C2 roles pre-existed. Added a **T05-specific, strict source-rendered-material acceptance contract** in `COOKER_REFERENCE_RENDER_MATERIAL_CRITIC_POLICY.json`, with validator and evidence generator at `tools/havenline/blender/t05_reference_material_critic.py`. The Godot/GLB/ref SHA evidence is packaged privately; never commit the original owner source to the repository. Note: `18567.png` is the owner's filename but the original image is **JPEG-encoded**; retain byte-for-byte SHA identity and verify its true format. At the current R26 candidate, independent visual C1/C2 critique and source-camera calibration are **NOT COMPLETE**, so the visual release gate remains **BLOCKED**, regardless of the verified 17/17 build and five real Godot 4K screenshots. The threshold is 9.5+ for every non-style visual axis and exact 10.0 for fidelity/language, with no averaging and zero unresolved defects. This focused threshold supersedes only the weaker interim `>9` wording for the cooker trial; it does not alter the repository-wide critic matrix or release standards.

