# HAVENLINE Permanent Reference-to-Native Material Critic Standard

**Applies to:** every game asset, every authored/runtime material or material variant, every task and all new scenes/biomes. Introduced 2026-10-27 on global pipeline **draft PR #103**. This is a **hard quality standard**, not a claim that existing assets have passed it.

## Why this is required

The owner explicitly rejected the T05 cooker R26 as far from reference `18567.png`, notwithstanding 17/17 technical model checks, nine preserved materials and real 4K isolated Godot screenshots. None of those technical results constitute source visual fidelity. The independent **C1 reference fidelity critic** and **C2 geometry/integrity critic** existed already, but recent cooker builds did **not** receive a source-locked, per-material independent verdict.

**Correct separation:** technical validation proves the candidate *renders*; the critic proves whether the candidate *looks like the source*. The owner's approval is a further independent requirement, not something a critic can override.

## Permanent authority hierarchy

1. Exact user-provided original reference images/video frames and Havenline A/B reference lock: always source-byte-bound and kept private where appropriate. File extensions are not proof of encoding (e.g. owner `18567.png` is JPEG-encoded); verify actual format and hash.
2. Actual **native Godot** candidate screenshots/frame sequences, tied to the exact source commit, scene, texture/material identity, and separate render run.
3. **Independent C1 and C2** visual critics in **separate execution runs**. Builder self-review, persona changes and synthetic fixtures are *not* independent critics.
4. User review and explicit acceptance after all mandatory visual dimensions pass. A user rejection takes precedence over any critic.
5. Shipping scene, full-view release census, physical Android performance and safety/UX checks remain separate mandatory gates.

## Hard scores

- `reference_fidelity = 10.0 / 10`, exact. No rounding or near-miss allowance.
- `visual_language = 10.0 / 10`, exact.
- Every other applicable axis must score **at least 9.5 / 10** from both critics: silhouette/proportions, surface palette/pattern, roughness/metallic/normal behavior, shaders/texture fidelity, seams/contact/occlusion, in-game readability, and cross-view consistency.
- There is **no averaging**, no minimum average, no threshold exception for speed or budget, and **zero unresolved visible defects**. Reviewers must give separate source-visible observations and actionable correction records.
- A single unresolved visible defect or user's explicit rejection means **BLOCKED** even when scores are high.

These thresholds specialize C1/C2 for **per-material visual art**; they do not reduce existing whole-frame 10/10 requirements or supplant C6/device performance.

## Profiles: require meaningful native views

| Asset type | Native Godot evidence | Additional requirement |
|---|---|---|
| 3D props, structures, characters, machines, resource models | Front, rear, left, right, three-quarter, overhead, **in-game-use** at 3840×2160 | Every actual material slot visible in specified views; all original source-visible surfaces matched |
| Terrain, snow, water, world scene materials | In-game, detailed-surface, wider context at 3840×2160 | Review substrate scale, seams, contact, UV repeats, interaction with surrounding surfaces |
| Dynamic shaders, particles, fire/smoke and VFX | In-game plus motion start/mid/end at 3840×2160 | Actual source-bound motion footage; static PNG screenshots alone cannot establish dynamic fidelity |
| UI and 2D scene visuals | In-game and detailed surface at 3840×2160 | Check color, hierarchy, glow, readability and style; no invented 3D backside reference required |

Physical-device full-game certification is additional and not implied by these evidence views.

## What each review must bind

A **private evidence workspace** carries the original reference bytes, source artwork/GLB/shader bytes, actual original Godot PNG files, scene/run metadata, source-camera registration justification and two raw reviewer JSON outputs. Each byte-bearing item has its own SHA-256. Every asset enumerates all its material IDs/variants, the exact source paths being modified/shipped, corresponding reference hash(es), and where the material is visible in the final screenshots.

The reviewer must explicitly inspect every listed material in context, not just source texture thumbnails or a composited sheet. A view whose material is hidden does not count as proof of that material. The reference camera must be aligned where source-visible comparisons are claimed. If a single owner image shows only one side, do **not** fabricate hidden-source geometry conclusions; use other views to assess continuity and whether the design remains coherent.

After individual materials pass, the full scene must separately pass the **whole-frame** reference critique so correct-looking components are not assembled into an incorrect image.

## Enforced source and release checks

**Global implementation:** `Docs/Production/GLOBAL_RENDERED_MATERIAL_CRITIC_POLICY.json` and `tools/havenline/production/global_rendered_material_critic.py`.

The CLI supports:

```bash
python3 tools/havenline/production/global_rendered_material_critic.py \
  private-evidence/manifest.json --root private-evidence --mode evidence

python3 tools/havenline/production/global_rendered_material_critic.py \
  private-evidence/manifest.json --root private-evidence --mode review

python3 tools/havenline/production/global_rendered_material_critic.py \
  private-evidence/manifest.json --root private-evidence --mode release \
  --expected-visual-paths-json expected-shipping-visual-paths.json \
  --report material-critic-release-report.json
```

- **Evidence mode** verifies source/capture/material coverage. It does *not* require C1/C2 and does *not* issue a review pass.
- **Review mode** requires complete real, independently issued C1/C2 raw files and per-asset scores. A synthetic test pass is **not** a visual review.
- **Release mode** additionally demands actual **shipping Godot scenes**, never only an isolated render. Final `shipping_visual_gate.py signoff` requires a matching public release **receipt** under `Docs/Production/MaterialCriticApprovals/{task_id}/{candidate_sha}.json`, SHA-linked from the VisualApprovals record; original owner imagery can stay in the private workspace. A public receipt is downstream governance, not itself a cryptographic signature on an inaccessible private model run.
- **T70 final game release** requires all shipped source material/visual paths to match a computed actual `HavenlineGodot/` census. Unreviewed existing material classes remain **BLOCKED**; a prior task label `APPROVED` does not create a new material critic pass.
- A governance-only policy change should not modify previously user-accepted game files. A changed/reopened candidate is reviewed under the new standard. All unchanged existing game material classes are still included in **T70** before final game release.
- Standalone programs, old synthetic test records, color-entropy checks, GLB validator scores, 4K pixel-change counts, and Blender viewport comparisons are **not independent material acceptance**.

## Permanent workflow for every new asset

**Reference lock → geometry and design → native Godot material captures → separate C1 and C2 critiques → prioritized defect corrections → repeat until 9.5+/10 and exact 10.0 style → owner signoff → shipping-scene/Android and whole-frame certification.**

Treat each critic finding as a modeling/material-design task, not as a reason to tune the prompt until a reviewer emits a passing score. If visual mismatch remains, the asset stays unapproved regardless of technical or performance passes. No release, no PR merge and no visual status promotion solely on the grounds that the automatic tests are green.

## Current cooker disposition

- **T05 R26 is owner-rejected as a reference match.** No actual independent C1/C2 material score exists for R26.
- The new global gate is a **permanent policy and implementation in draft global PR #103**; it will not be effective on a protected main/release branch until reviewed, merged and wired as a required CI check/branch rule.
- T05 PR #101 is separate. Its original `18567.png` owner reference and private independent-review package stay outside public GitHub.
- The nearest meaningful cooker milestone is a strongly more faithful snow roof, correctly sculpted saw assembly, hand-finished woodwork and organic raw/cooked food shapes—not another infrastructure-only technical pass.
