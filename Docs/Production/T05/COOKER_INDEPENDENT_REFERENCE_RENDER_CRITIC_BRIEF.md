# T05 Cooker — Independent Reference / Rendered Material Critic

**This is a separate visual review, not the builder's self-assessment.** Do not report 9.5/10 or 10/10 simply because the asset exported, has texture maps, passed 17 technical checks, or produced 4K Godot frames.

## Authoritative input

- Owner's original file **18567.png**, exact SHA-256 `729393f7980d8bd70906a7e4de04c3c6b21de5dfe4deb3d98ca7005b54d61635`, visually 1536×1536 and **internally JPEG encoded** despite its .png name. The original image must remain private.
- **Actual 3840×2160 Godot frame pixels** at front, three-quarter, right, rear and reverse-quarter, all SHA-tied to the same candidate GLB. The studio Blender stills are ancillary, not authoritative for in-game materials.
- Actual exported GLB with original nine surface slots and embedded base color maps for wood, wood_light, blue, metal, red and snow. Evaluate final rendered material response (lighting, contrast, roughness, metalness and shadow), not just the source texture pictures.
- Current R26 evidence: source-build run `40523998873`, isolated Godot run `40524651335`, GLB SHA `c2832480371df482e2f0b6192feab733b3112209b2c4e47b7a09886a22f3f35c`. **This is not the shipping Godot scene.**

## Visual-first audit procedure

1. Verify raw original and each native capture hash before looking at a preview sheet.
2. Establish camera/source silhouette comparability. The owner render contains only one viewing angle; do not claim unseen side/back geometry has a definitive source pixel counterpart. If camera alignment cannot be justified, **fail closed** instead of assigning an exact-source match score.
3. Review individual close-up original regions: (a) snow pillow and overhang/chimney, (b) steel arched saw window and fasteners, (c) left timber bin and irregular marbled raw meat, (d) right steel tray, cooked cuts and tight orange binding, (e) load-bearing wooden crate with steel corner hardware, (f) visible warm white smoke.
4. For each visible region, compare **shape first**, then materials/color/pattern, sculpted highlights and roughness, local shading, occlusion and proper contact. Call out wrong proportion, silhouette, missing detail, color/material mismatch, generic shapes or clipping separately.
5. Inspect the complete actual Godot result from every camera for back/side consistency, floating geometry, missing surfaces, seams, texture bleeding and changes in material appearance. Do not credit arbitrary procedural detail that is inconsistent with the owner's image.
6. Record direct observations and actionable defects with location and which file/view demonstrates each one; no speculative claims of unseen proof.
7. Score each of 13 categories **independently** using `COOKER_REFERENCE_RENDER_MATERIAL_CRITIC_POLICY.json`: exactly **10.0** for `reference_fidelity` and `visual_language`; at least **9.5** for every other category. **Never average** a weak axis into a passing result. A remaining defect means BLOCKED regardless of any raw score.
8. Keep source-camera registration evidence, complete coverage, independent reviewer identity/model, separate execution run ID, raw reviewer JSON and SHA-bound GLB/manifest identity. A builder's alternate persona does not qualify as independent.
9. Produce correction priorities in descending visual impact. Scores should drive actual sculpting and improved native renders, not the opposite. Do not claim reviewer pass from a filled template or synthetic regression-test numbers.

## Current source-visible issues to actively challenge

- R26 snow remains broad and angular compared with thick layered reference snow; overhang/body seam remains a concern.
- The window/saw looks simplified and flatter than the deep silver framed enclosure with intricate metal joints.
- Food portions and marbling/straps remain geometric and less hand-finished than source; material maps do not fix shape alone.
- Upper blue housing and lower timber/steel crate lack the reference's deep crafted joinery and steel trim hierarchy.
- The owner source includes prominent billowing chimney smoke, which the static R26 isolated renderer does not produce.
- Source camera and native Godot scene lighting are not fully matched; do not mistake framing/lighting differences for confirmed material improvements.
  
A skeptical, specific **failure** is valuable feedback. Do not optimize prompts to produce passing numbers. Independent acceptance is separate from owner approval, shipping-scene integration, C6 and sustained real-device Android performance.

## Integration

Private reviewer input is assembled with `tools/havenline/blender/t05_reference_material_critic.py prepare`. When an actual independent raw review exists, run `... validate --package <private_unpacked_evidence> --review <authentic_independent_review.json>`. The validator intentionally rejects absent source-camera evidence, missing views or shader slots, low per-category scores, self-review and missing raw independent results. Synthetic CI verifies these safeguards without exporting original owner artwork to GitHub.
