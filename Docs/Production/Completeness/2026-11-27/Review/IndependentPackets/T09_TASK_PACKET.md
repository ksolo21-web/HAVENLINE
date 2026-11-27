# Havenline frozen task packet — T09

Generated: 2026-11-27T12:46:06.382372+00:00

## Identity
- Task ID: T09
- Task name: Harvesting and automatic acquisition
- Workstream ID: T09-harvesting-acquisition-builder
- Owner: harvesting-acquisition-builder
- Isolated branch: havenline/T09-harvesting
- Exact base integration commit: 7492074e40a0b061f31d8c32602b7a581b2610f3

## Dependencies
Required APPROVED upstream tasks: T06, T07, T08

## Owned paths
- `HavenlineGodot/assets/harvesting_v1/**`
- `HavenlineGodot/scripts/harvest_presentation.gd`
- `HavenlineGodot/tests/test_task09_harvesting.gd`
- `HavenlineGodot/tests/test_task09_integration.gd`
- `HavenlineGodot/tests/capture_task09_harvesting.gd`
- `HavenlineGodot/tests/capture_task09_performance.gd`
- `Docs/Production/T09/**`
- `tools/havenline/task09/**`
- `.github/workflows/havenline-task09-*.yml`

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
- **C2 — Technical / Visual Integrity Critic**: `tools/havenline/production/critic_harness.py validate-raw --critic C2`; dimensions: geometry_contact, clipping_seams, intentional_gap_integrity, cross_view_integrity.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Validates evidence retained by an actual separate agent/model review; this command does not perform or invent the visual review.
- **C3 — Havenline Gameplay Identity Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: havenline_identity, simple_context_controls, physical_core_loop, complexity_discipline, world_response_readability.
  - evidence categories: gameplay_state, control_state, loop_evidence
- **C4 — Gameplay UX / Readability Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: interactable_clarity, danger_clarity, collection_feedback, resource_destination, world_change_clarity, next_action_clarity.
  - evidence categories: gameplay_state, feedback_state
- **C5 — Motion / Rigging Critic**: `tools/havenline/production/specialist_critic_runner.py`; dimensions: full_cycle, foot_contact, lower_body_mechanics, upper_body_mechanics, weight_transfer, transitions, clipping, secondary_motion_contact.
  - required capture harness: `tools/havenline/production/motion_capture.py`
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - evidence categories: motion_cycle, motion_transition, contact_detail
  - final approval unavailable through this runner: A separate source-bound independent review must actually inspect the full motion cycles and transitions through playback. This contact-sheet runner cannot grant final C5 approval.
- **C6 — Performance Critic**: `tools/havenline/production/critic_harness.py ingest-performance-review`; dimensions: frame_time, draw_calls, geometry, texture_memory, shader_cost, physics, animation, population, thermal_risk.
  - current evidence contract: `Docs/Production/EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`
  - execution scope: Current final evidence combines unchanged independent scores and exact hash-bound measurements. The measurement gate alone cannot approve the critic.

## Resource / tool / actor / animation contract
- REQUIRED by `Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md`.
- Resource registry SHA256: `8e9feba3a92972b10ac7dc8589e43bd0f988c2981ffe0fcace2edb1100e3bd9d`
- Actor capability matrix SHA256: `f319469be543267c6a21988d6b23f915550bd01c7d8513516b7410915680b1bf`
- Animation action matrix SHA256: `57df079f213a88e58b87e01aa7b520ca2fe4d98a41368307fdbba433a57d46e5`
- Resources this task must resolve/prove: wood, stone, metal, fuel
- Actor capability keys this task must prove: player_lead, core_human_companion, rescued_survivor_helper
- Animation profiles this task must prove: human_player_chop, human_player_mine, human_player_dismantle
- Run `python3 tools/havenline/production/resource_actor_contract.py --task T09 --manifest <candidate-manifest> --output <proof.json>` before closure.

## Registered forward contracts
- none registered for this task.

## Whole-game stakes, useful companions and resource value

Forward requirements: `Docs/Production/GAMEPLAY_DEPTH_STANDARD.md` and `GAMEPLAY_DEPTH_CONTRACT.json`. This addendum does not reopen frozen historical scope, change dependencies/ownership, activate a task, or certify runtime behavior. Use the existing scope/change process for a changed approved component. Owner/consumer labels are responsibilities, not new dependency edges.

- **GD03 — Complete survivor assistance (consumer)**: Provide a trained/equipped survivor path for every physical human task family in ACTORS_MOTION_REQUIREMENTS.json. Specialization changes competence and preference; missing capabilities cannot silently become permanent exclusions. Evidence: Ten-family actor/action coverage; Complete work-to-destination scenarios; Region/equipment eligibility and explicit exceptions; Role-appropriate full motion.
- **GD05 — Useful large mixed survivor loads (consumer)**: Use shared typed custody and large useful mixed carrying with readable stacks. Preserve unlimited logical player inventory; explicitly reconcile finite/upgradable worker capacity before choosing its values. Evidence: Capacity-policy decision with real trip/throughput evidence; Partial/full multi-type transfer conservation; Loaded turns and two-gate clearance; Upgrade and visual stack compression proof.
- **GD09 — Full state/action/transition animation (consumer)**: Cover the twelve animation families, complete loops, transitions, contact, interruption, blocked/full/empty and resume states. Use justified static/shared dispositions where appropriate; no generic placeholder masquerades as finished action. Evidence: Action/state inventory linked to actual clips/mechanisms; Real-time and slow playback from distinct meaningful views; Feet/toes/knees/hands/paws/tails/wings/tool/cargo contact; State-to-authoritative-event alignment.
- **GD12 — Action-complete audio and accessible feedback (consumer)**: Feature owners emit truthful event phases; T54 freezes cue/mix/music/ambience or justified silence and listening evidence for each applicable event, variant and interruption. Critical information remains readable muted/reduced motion. Evidence: Per-event sound/music disposition; Actual listening under busy mixed activity; No success sound on denied/replayed transaction; Priority/concurrency/accessibility evidence.
- **GD13 — Every shipped material has a meaningful purpose (consumer)**: Each introducing feature freezes acquisition, actual identity/alias, processing, primary use, payoff, demand, availability/cost, custody and surplus/retirement. T33 later validates the combined economy; it is not an added circular prerequisite to earlier producers. Evidence: Resource-value ledger and actual ID bindings; One demonstrable useful outcome per shipped ID; Recipe/source/sink/phase coverage; No undeclared concept-to-item conversion.
- **GD14 — Resource and render reconciliation (owner)**: Reconcile six canonical IDs, current-foundation IDs, thirteen base and twenty expansion render rows. Keep variants, containers and unselected concepts separate from canonical economy IDs; preserve all assets and decisions. Evidence: Exact source/render commit/path/hash inventory; Explicit alias/use/defer/exclude disposition per concept; Current foundation coal/slate/metal, processed-output and cash gaps resolved by owner evidence; No recipe/drop/price inferred from a still.

Task-specific actor/motion details:

- Human method/tool parity for every registered opening resource; distinct full work cycles and impact authority.

Unfrozen design decisions for this owner:

- D03 — Exact material recipes and aliases: RECOMMENDED_PENDING_OWNER_FREEZE_AND_PLAYTEST. Freeze Fuel/coal and metal/ore mapping; Food eligibility and processing; Slate/steel/planks/blocks and surplus uses; Regional material identities.

Use the complete source-bound resource ledger and actor scenarios under `Docs/Production/GameplayDepth/2026-11-27/`. The introducing task freezes a useful resource contract before its own integration; T33 later reconciles it. Each pet proves standalone usefulness before T31 integration. All future play scenarios remain untested by this planning audit. Preserve the existing >=9.9 and stronger exact-10 reference rules.

## Current whole-game decisions and gap closure

Read `Docs/Production/COMPLETENESS_STANDARD.md`, `WHOLE_GAME_COMPLETENESS.json` and `CURRENT_GAMEPLAY_SOURCE.json`. The CD choices supersede the earlier D01–D05 open behavior wording; numeric tuning and actual game evidence remain open. These responsibilities are not new dependency edges or task activation, and preserve frozen historical scope.

- **CG02 — All-task survivors and large mixed carrying (consumer):** Use player-like unlimited logical cargo and all ordinary physical job families, including all authorized plots/conveyors and ordinary-cash buying; retain budgets and equipment truth. Required evidence: All ten human task families demonstrated.; Large mixed load conserved through service/payment/combat/reload.; No basic-AI paygate or autonomous premium spend.
- **CG04 — Combat roster, useful counters and equipment (consumer):** Use selected bounded hostile/hunt/weapon roster and existing GitHub art. New variants require declared source and proof; extra HP alone is not a distinct enemy behavior. Required evidence: Real telegraph/contact/miss/recovery/counterplay per selected enemy and weapon.; Friendly pets and rescue candidates never become hunt drops.; No protected-actor attack exploit or reset loot at sanctuary; exposed perimeter defenses follow their declared valid domain.
- **CG09 — Materials, money and real demand (owner):** Bind actual raw/product/currency IDs to named uses; coal/slate/metal/planks/blocks and cash receive real spending/processing sinks. Concepts have explicit selected/alias/reserve roles. Required evidence: Useful source-to-use-to-payoff loop for every shipped ID.; One ordinary currency and one primary premium currency; custody locations are not wallets.; No fake aliases or recipe facts inferred from art.; Ordinary cash conservation includes committed spending: cash sources equal till+pocket+house+committed outflow, so a new debit cannot reappear in a derived till balance.
- **CG10 — Shortage, surplus and renewable recovery (consumer):** Each progression dependency has reachable free sources, renewable or sufficient finite supply, useful surplus disposition and conserved conversions. Required evidence: Zero-stock, depleted-source, repeated-failure and no-worker routes.; No infinite profitable conversion, stranded paid balance or compulsory event input.
- **CG14 — Complete action, machine and sound states (owner):** Prove complete start/work/contact/success/miss/blocked/empty/full/cancel/recovery transitions for every applicable actor, machine, tool and transport. Use actual clip/contact/audio bindings. Required evidence: Full cycles and transitions from meaningful angles, feet/toes/knees, attachments and clipping.; Actual sound listening in busy play; mute/reduced-motion equivalents.; No success sound or transfer effect for denied/replayed transaction.
- **CG15 — Reference and render fidelity at every use state (consumer):** Use pinned selected GitHub references with explicit observed/authored/inferred distinctions. Current candidate must meet>=9.9 reference dimensions and every stronger exact10 visual rule; historical static scores do not pass runtime. Required evidence: Exact image/model/rig/scene/clip/source identity.; Actual matched-camera play and full motion evidence; no average hides a failed area.; Missing source or tiny unidentified figure stays unresolved rather than guessed.
- **CG16 — One unambiguous gameplay continuation source (consumer):** Use CURRENT_GAMEPLAY_SOURCE.json and corrected root entrypoints: newer Codex field project; main/alfred commands are explicitly historical. Resolve actual live head and owner before edits. Required evidence: Entry-point guidance agrees on branch/project/scene.; No runtime merge, branch reassignment or historical receipt rewrite.

Applicable selected decisions: CD01, CD03, CD05, CD06, CD08, CD12.
Use the 100 authored outcomes, seven attack/specialty/render bindings and ten transaction boundaries in `Completeness/2026-11-27/`. All gameplay scenarios remain unrun by this audit. Current reference >=9.9 and stronger exact-10 visual requirements still apply.


## Current score policy
Every mandatory dimension >= 9.5 unrounded; reference-sensitive dimensions >= 9.9; C1,C2,C3,C4,C5,C11 every mandatory dimension exactly 10.0; no averaging or rounding; complete evidence; zero mandatory defects


## Score rule
Use Docs/Production/REFERENCE_ACCEPTANCE_POLICY.json and REFERENCE_ACCEPTANCE_STANDARD.md.
Final reference-sensitive dimensions >=9.9 unrounded; preserve all stronger exact-10 visual gates.
Other mandatory specialist dimensions >=9.5. A reference-sensitive 9.5 is interim only.
No averaging, rounding, missing evidence or unresolved mandatory defects. Freeze the input manifest's
reference_sensitive_dimensions per critic before review; the reviewer cannot omit them.

## Critic independence
C1/C2 and every specialist critic marked independent-model-required must run in a separate review job/runtime. A builder prompt, persona swap, or self-review never qualifies. If the zero-cost independent runtime is unavailable, construction/testing may continue but approval remains BLOCKED.

## Evidence
Exact-source hashes, changed-file manifest, deterministic engine views, performance records, applicable save/device matrices, raw critic inputs/outputs, deterministic supplements, known failures and final dispositions are mandatory before APPROVED. Use `specialist_evidence_manifest.py` for static C3/C4/C7/C8/C10/C11 inputs and interim C5 screening. Final C1/C2/C5 and scored C6 evidence follow `EXTERNAL_INDEPENDENT_REVIEW_TRANSPORT.md`; C9 uses the actual `security_exploit_harness.py` attack transport. Approval provenance must satisfy the V3.1 retention policy, and T10+ closeout must retain its exact terminal `factory-observation.json` and pass `factory_closeout_gate.py`.

## Scope
Use the authoritative task-specific frozen scope when present. This generated packet does not expand runtime scope.
