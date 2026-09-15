# Havenline frozen task packet — T08

Generated: 2026-09-15T17:16:28.109153+00:00

## Identity
- Task ID: T08
- Task name: Visible inventory, physical carrying and transfers
- Workstream ID: T08-physical-inventory-builder
- Owner: physical-inventory-builder
- Isolated branch: havenline/T08-visible-inventory
- Exact base integration commit: 7744b9f6a063da3385ce10992ef732ba2c669890

## Dependencies
Required APPROVED upstream tasks: T05, T06, T07

## Owned paths
- `HavenlineGodot/scripts/carry_stack.gd`
- `HavenlineGodot/scripts/storage_stockpile.gd`
- `HavenlineGodot/scripts/transfer_feedback.gd`
- `HavenlineGodot/tests/test_task08_inventory.gd`
- `HavenlineGodot/tests/test_task08_integration.gd`
- `HavenlineGodot/tests/capture_task08_inventory.gd`
- `Docs/Production/T08/**`
- `tools/havenline/task08/**`
- `.github/workflows/havenline-task08-*.yml`

## Protected paths
- `HavenlineGodot/assets/reference_forest/**`
- `HavenlineGodot/scripts/reference_forest.gd`
- `HavenlineGodot/scripts/river_geometry.gd`
- `Docs/Production/T01/**`
- `Docs/Production/T02/**`
- `HavenlineGodot/scripts/main.gd`
- `HavenlineGodot/scripts/simulation.gd`
- `HavenlineGodot/scripts/population_simulation.gd`
- `HavenlineGodot/scripts/outpost_simulation.gd`
- `HavenlineGodot/scripts/outpost_view.gd`
- `HavenlineGodot/data/reference-contract.json`

## Acceptance gates
- G1: REQUIRED unless this packet records explicit N/A rationale.
- G2: REQUIRED unless this packet records explicit N/A rationale.
- G3: REQUIRED unless this packet records explicit N/A rationale.
- G4: REQUIRED unless this packet records explicit N/A rationale.
- G5: REQUIRED unless this packet records explicit N/A rationale.
- G6: REQUIRED unless this packet records explicit N/A rationale.
- G7: REQUIRED unless this packet records explicit N/A rationale.
- G8: REQUIRED unless this packet records explicit N/A rationale.
- G9: REQUIRED unless this packet records explicit N/A rationale.
- G10: REQUIRED unless this packet records explicit N/A rationale.
- G11: REQUIRED unless this packet records explicit N/A rationale.
- G12: REQUIRED unless this packet records explicit N/A rationale.
- G13: REQUIRED unless this packet records explicit N/A rationale.
- G14: REQUIRED unless this packet records explicit N/A rationale.

## Required critics and executable safeguards
- **C2 — Technical / Visual Integrity Critic**: `existing task-scoped C2 reviewer`; dimensions: geometry_contact, clipping_seams, intentional_gap_integrity, cross_view_integrity.
- **C3 — Havenline Gameplay Identity Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: havenline_identity, simple_context_controls, physical_core_loop, complexity_discipline, world_response_readability.
  - evidence categories: gameplay_state, control_state, loop_evidence
- **C4 — Gameplay UX / Readability Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: interactable_clarity, danger_clarity, collection_feedback, resource_destination, world_change_clarity, next_action_clarity.
  - evidence categories: gameplay_state, feedback_state
- **C6 — Performance Critic**: `tools/havenline/production/critic_harness.py performance`; dimensions: frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population, thermal_risk.

## Resource / tool / actor / animation contract
- REQUIRED by `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`.
- Resource registry SHA256: `b8912b83c724f7c52e2ad9ecc05786d483fcc9741aa9bf8db8c4e31d64d05df8`
- Actor capability matrix SHA256: `f319469be543267c6a21988d6b23f915550bd01c7d8513516b7410915680b1bf`
- Animation action matrix SHA256: `57df079f213a88e58b87e01aa7b520ca2fe4d98a41368307fdbba433a57d46e5`
- Resources this task must resolve/prove: none predeclared; any introduced resource must still be registered
- Actor capability keys this task must prove: none predeclared
- Animation profiles this task must prove: none predeclared
- Run `python3 tools/havenline/production/resource_actor_contract.py --task T08 --manifest <candidate-manifest> --output <proof.json>` before closure.


## Score rule
Every applicable mandatory reviewed dimension must be strictly >9.0 unrounded.
Target 10/10. No averaging and no unresolved mandatory defects.

## Critic independence
C1/C2 and every specialist critic marked independent-model-required must run in a separate review job/runtime. A builder prompt, persona swap, or self-review never qualifies. If the zero-cost independent runtime is unavailable, construction/testing may continue but approval remains BLOCKED.

## Evidence
Exact-source hashes, changed-file manifest, deterministic engine views, performance records, applicable save/device matrices, raw critic inputs/outputs, deterministic supplements, known failures and final dispositions are mandatory before APPROVED. Use `specialist_evidence_manifest.py` for C3/C4/C5/C7/C8/C10/C11; C9 uses `security_exploit_harness.py`.

## Scope
Use the authoritative task-specific frozen scope when present. This generated packet does not expand runtime scope.
