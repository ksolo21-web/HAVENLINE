# HAVENLINE — Unity Project Context

This file is the authoritative continuity record for AI-assisted work on HAVENLINE. Read it before substantial changes. Do not depend on chat memory alone when this file is available.

## Non-negotiable working rule

**Work through failures and blockers. Do not get stuck.**

When a tool, conversion, package, render path, import path, build step, or validation approach fails:

1. Diagnose the failure.
2. Preserve good existing work.
3. Try a reasonable alternate route or fallback.
4. Reject experiments that make the result worse.
5. Continue progressing until reasonable paths are exhausted.
6. Never claim a blocked or unverified result passed.

A failed approach is not permission to stop if another credible path remains.

## Project presentation

- Shipping gameplay is landscape-only.
- Gameplay camera/readability decisions must be judged in the shipping landscape view.
- Character readability at gameplay scale matters; do not approve characters only from close-up asset inspection.
- Preserve existing working gameplay and project architecture while improving assets and systems.

### Production visual bar

- HAVENLINE is being built to a premium AAA-style Android presentation bar, not a prototype/greybox bar.
- Do not ship visible placeholder, greybox, generic-player, block-built, default-material, or SampleScene content.
- Visible environment, shelter, furnace, resource, defense, and character geometry must read as authored production art rather than Unity primitives/blockouts.
- The shipping camera should preserve the established close landscape orthographic/isometric readability: the player must remain clearly readable while the inhabited camp, furnace, shelters, storage, resources/helpers/defenses, and immediate action space remain legible.
- HUD presentation stays compact and gameplay-first. Do not regress to giant permanent cards, oversized action-button decoration, or a large artificial warmth circle.
- Warm furnace lighting against a colder snowy environment, atmospheric depth, controlled bloom/color grading, readable materials, and restrained winter motion/effects are part of the visual identity; effects should enhance the scene rather than hide low-detail art.
- Real C1–C4 Humanoid characters are required for the production path. A shipping build must never silently substitute an old generic/blocky player.
- Visual claims require proof from the real Unity shipping scene/camera. A technically passing build is not visually approved merely because tests or static contracts pass.

## Character roles

- Character 1 and Character 2 are the two playable lead options.
- Whichever of Characters 1 or 2 the player does not select becomes a helper/companion.
- Characters 3 and 4 are companion/helper characters.

## Current character checkpoint: V7

Status: **machine-valid and synthetic-pose-valid staging candidates; not final and not human-approved.**

Do not silently downgrade to an older checkpoint.

### Character 1

- V7 file: `Havenline_Character_1_Rigged_Refined_V7.glb`
- SHA-256: `a14352ab6fb483609c91712dceab6a3be8ae35ae6c3733e431df49de3f9c55db`
- Size: 9,149,476 bytes
- 52-joint humanoid skin retained.
- Carries forward the approved blue bedroll/strap geometry from V5.

### Character 2

- V7 file: `Havenline_Character_2_Rigged_Refined_V7.glb`
- SHA-256: `6252680d0fd990f8d6819b6255e1d9b13c7ff77c34eacb84551efcad6d1dc839`
- Size: 9,799,036 bytes
- 52-joint humanoid skin retained.
- Strong V4/V5 direction intentionally preserved rather than forcing unverified cosmetic changes.

### Character 3

- V7 file: `Havenline_Character_3_Rigged_Refined_V7.glb`
- SHA-256: `88ecef677472ed63fce98f0e75e60507555dd9d8becfb75aa02f59f59eb4d360`
- Size: 10,931,132 bytes
- 52-joint humanoid skin retained.
- Visual geometry includes separate burgundy shirt, cream vest, orange open-coat trim, and brass button geometry.
- Shirt/vest/open-coat trim use exact nearest-underlying-base-surface skin weights.
- Brass buttons retain V5 weights.
- Synthetic pose validation passed.
- Combined pose mean surface-offset change: about `0.0000459493` model units.
- Combined pose max surface-offset change: about `0.000231377` model units.

### Character 4

- V7 file: `Havenline_Character_4_Rigged_Refined_V7.glb`
- SHA-256: `bea67fe847c2c1f05bd0a0822cbca4b16b95f6e844a1d9aba66f56b2dc374a6e`
- Size: 10,884,332 bytes
- 52-joint humanoid skin retained.
- Carries forward V5 headband and hoop-earring fidelity geometry.

## Rejected character experiments

Do not reintroduce these without a materially different method and new proof:

- Closed torus curl overlays — visually read as artificial rings/flowers.
- Open C-shaped procedural curl overlays — still looked artificial.
- V6 Character 3 manual torso-only garment skinning — structurally valid but failed deformation/pose-drift QC.
- Texture/UV hacks that leak garment colors onto unrelated islands or create patchy triangles.

## Unity truth gate

A character is **not final** merely because a GLB parses, validates structurally, or looks acceptable in a non-Unity inspection.

Before final approval/promotion, require the strongest available evidence:

1. Deterministic import/conversion into the HAVENLINE Unity review/production path.
2. Unity URP front, 3/4, side, and back proof renders.
3. Animated torso/arm/head stress poses for clipping and deformation review.
4. Gameplay-scale proof in the shipping landscape camera.
5. Side-by-side human visual review against the approved turnaround artwork.
6. No approval flag until those checks pass.

The historical production contract expects:

`Assets/Havenline/Art/Characters/Production/CharacterN/CharacterN_production.fbx`

V7 GLBs are staging/review sources and must not be falsely renamed or promoted as production FBX files just to satisfy a filename check. If direct GLB import is used for review, keep the promotion gate explicit.

## Current Unity project facts

- Unity Editor: `6000.5.6f1`
- URP package: `17.5.0`
- Unity AI Assistant package is present in the project.
- Current V7 review work is on branch `agent/havenline-v7-unity-review`.
- Direct Unity GLB review/import support is being used to avoid making Blender/FBX conversion a single point of failure.

## Validation discipline

- Preserve a baseline before changing working assets.
- Distinguish pre-existing failures from regressions introduced by the current change.
- Compilation is necessary but not sufficient.
- Do not claim visual correctness without visual proof.
- Do not claim animation correctness from static meshes.
- Do not claim gameplay readability from close-up character renders.
- Do not claim build/device performance without actual measurement.
- If live Unity Editor access is unavailable, continue with repo-side preparation, static validation, deterministic tooling, CI where possible, and artifact staging rather than stopping; report the remaining live-editor gate clearly.

## Recovery rule for future sessions

At the start of future HAVENLINE work:

1. Read this file.
2. Inspect the current branch/repository state.
3. Check for newer validation reports or approved checkpoints before assuming V7 is still latest.
4. Continue from the newest proven state.
5. Apply the blocker rule above automatically.

Repository evidence overrides stale conversational summaries.
