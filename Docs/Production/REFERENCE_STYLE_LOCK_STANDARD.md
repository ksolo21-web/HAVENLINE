# HAVENLINE Reference Style Lock Standard

## Authority

This is a mandatory global visual contract. Every in-game material or surface treatment created or modified for HAVENLINE must match the locked reference style at **100% fidelity / 10.0 out of 10**. There is no lower style threshold, exception, substitute style, performance waiver, schedule waiver, or "close enough" pass.

The primary authority remains:

1. `Docs/Design/ReferenceVideoLock/REFERENCE_VIDEO_LOCK.md`
2. `Docs/Design/ReferenceVideoLock/reference-video-sources.json`
3. the actual pixels/motion from locked recordings A and B

The supplemental Whiteout Survival ad pack is additional style/interaction evidence. It may refine understanding, but it may never override a conflict with the locked A/B recordings or HAVENLINE identity.

## Scope — every visible gameplay material

The lock applies to every new or modified appearance treatment visible in gameplay, including snow, ice, water, terrain, soil, paths, work floors, wood, stone, metal, cloth, leather, fur, feathers, skin, hair, fences, buildings, stations, machinery, tools, weapons, defenses, vehicles, resources, food, money, carried stacks, stockpiles, pads, characters, survivors, customers, companions, hostiles, textures, colors, decals, outlines, normals, roughness, metallic/specular, emission, transparency, shaders, procedural materials, particles, VFX, and lighting/post-processing that materially changes surface appearance.

"Different object" is not permission for a different visual language. Unshown objects must extend the locked reference grammar: bright polished stylized 3D, clean sculpted forms, readable silhouettes, coherent soft/contact shadows, white/blue winter masses, warm work zones, saturated gameplay accents and finished non-debug surfaces.

## Exact acceptance rule

For any candidate that creates or changes a gameplay visual material:

- C1 is mandatory even if the task's normal archetype would not otherwise require C1.
- C1 `reference_fidelity` must equal **10.0 exactly**.
- C1 `visual_language` must equal **10.0 exactly**.
- C1 must report zero style defects and complete evidence coverage.
- A complete material/style inventory must bind every material-affecting changed path to source-bound visual evidence.
- Actual reference pixels must be reviewed. Prose descriptions alone cannot satisfy the lock.
- No averaging may hide a lower style score.
- Technical optimization must preserve the reference appearance; performance pressure is solved by implementation efficiency, not by lowering style fidelity.
- Placeholder/default/debug material is an automatic failure.

The general critic rule remains strictly greater than 9.0 for other mandatory dimensions. This lock only **strengthens** reference-style acceptance; it lowers nothing elsewhere.

## Drift prevention

The deterministic validator `tools/havenline/production/reference_style_lock.py` detects material-affecting changes from asset/shader/scene paths and material-producing script tokens. A candidate with detected visual-material changes fails closed unless its candidate manifest contains a valid `reference_style_lock` proof block.

If an existing off-style material becomes visible while reviewing a candidate, it is a mandatory defect. If that material is outside the current workstream's ownership, create a bounded change request rather than silently ignoring it or editing a foreign-owned path.

Governance adoption alone does not invalidate the immutable already-accepted source SHAs enumerated in `REFERENCE_STYLE_LOCK.json`. This is exact-source invalidation discipline, **not a task waiver or shipping exception**: preservation applies only when task + candidate SHA exactly match that historical list. Any reopened task, replacement candidate, new material-affecting SHA, or changed visual source is fully subject to the 10/10 lock. T70 must run a full shipped-material census so even historically preserved material cannot ship if it drifts from the locked reference style.

## Evidence contract

The candidate's style evidence JSON must contain the exact `task_id` and `candidate_commit`, `coverage_complete: true`, `reference_pixels_reviewed: true`, primary references A and B, the exact detected material-affecting changed paths, a non-empty material inventory for an applicable candidate, `known_style_defects: []`, and `full_release_census: true` for T70.

The evidence file, policy file, reference lock and source manifests are SHA-256 bound in the candidate manifest. Style evidence is source-bound and cannot be reused after a material-affecting source change.

## Repair and invalidation

A style repair invalidates C1/reference-style proof and any other critic/evidence whose actual inputs changed. It does **not** automatically invalidate unrelated same-source passes. Conversely, critic-specific invalidation can never preserve C1/style proof across a changed material-affecting source SHA.

## Builder rule

When a task requires a material not literally shown in the references, do not improvise a new aesthetic. Derive it from the reference grammar, capture it in gameplay context and close the candidate only after exact 10/10 C1 style fidelity is proven.
