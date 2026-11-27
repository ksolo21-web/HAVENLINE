# Havenline frozen task packet — TEMPLATE

> Generate a task-specific copy with `python3 tools/havenline/production/task_packet.py TASK_ID`.
> A packet freezes construction scope; it never self-approves production.

## Identity
- Task ID:
- Task name:
- Workstream ID:
- Owner:
- Isolated branch:
- Exact base integration commit:
- Packet generation timestamp/build ID:

## Dependencies
- Required APPROVED upstream tasks:
- Required stable interfaces:
- Dependency evidence paths:

## Frozen scope
### Required behavior
-

### Explicit exclusions
-

### Havenline identity constraints
- Preserve one-primary-joystick/simple-context philosophy.
- Preserve MOVE → AUTO-INTERACT → GATHER → VISIBLY CARRY → DELIVER → TRANSFORM → RESCUE → BUILD/UPGRADE → EXPLORE → DEFEND.
- No unauthorized control/menu complexity.
- No unrelated future-task implementation.

## Path ownership
### Owned production paths
-

### Protected/foreign-owned paths
-

### Integration-only paths
-

If an owned-path conflict is discovered, STOP modifying that path and create a
structured request in `Docs/Production/ChangeRequests/`.

## Acceptance gates
Mark every applicable gate REQUIRED or N/A with rationale.

- G1 DEPENDENCY
- G2 PATH-OWNERSHIP
- G3 SCOPE
- G4 BUILD/IMPORT
- G5 FUNCTIONAL
- G6 REGRESSION
- G7 EVIDENCE-PROVENANCE
- G8 PERFORMANCE-BUDGET
- G9 PERSISTENCE
- G10 SECURITY/ECONOMY
- G11 ACCESSIBILITY/ADAPTIVE-UI
- G12 CRITIC-COVERAGE
- G13 SCORE (current REFERENCE_ACCEPTANCE_POLICY: reference-sensitive final dimensions >=9.9, existing visual exact-10 gates preserved, other mandatory specialist dimensions >=9.5; unrounded, no averaging, complete independent evidence; a reference-sensitive 9.5 result is interim only)
- G14 INTEGRATION

## Whole-game stakes, companions and resource value

Resolve the task's forward addendum using `python3 tools/havenline/production/gameplay_depth.py task TASK_ID` and the [gameplay-depth standard](GAMEPLAY_DEPTH_STANDARD.md).

- Applicable GD requirement IDs and owner/consumer responsibilities:
- Specific actor/motion requirements and source-bound render selections:
- Meaningful source/use/payoff and custody proof for each introduced item/currency:
- Failure/recovery, full-cycle animation and intelligent-assistance scenarios:
- Unfrozen decisions, selected values, rationale and normal-play evidence:
- Exact candidate evidence and unresolved defects:

Owner/consumer labels do not create dependency edges or change frozen historical scope. Introducing tasks resolve their own resource/job obligations before integration; T33/T31 later reconcile/integrate. The planning checker cannot certify runtime or approve a task. Use existing change/scope processes for changes to previously approved work.

## Current selected decisions and gap closure

Run `python3 tools/havenline/production/completeness.py task TASK_ID` and follow [COMPLETENESS_STANDARD.md](COMPLETENESS_STANDARD.md).

- Applicable CG owner/consumer obligations and selected CD decisions:
- Current source selector, live head and ownership reconciliation:
- Relevant authored level outcomes, pet attack/specialty/render bindings and transaction boundaries:
- Remaining numeric tuning, implementation evidence and known defects:

Selected CD behavior supersedes earlier D01–D05 open behavior wording. This is forward planning, not task activation or gameplay approval; retain frozen scope and existing dependencies.

## Resource / tool / actor / animation contract
Mark REQUIRED or N/A from `RESOURCE_ACTION_REGISTRY.json`.

When REQUIRED, record:
- `RESOURCE_ACTION_REGISTRY.json` SHA256:
- `ACTOR_CAPABILITY_MATRIX.json` SHA256:
- `ANIMATION_ACTION_MATRIX.json` SHA256:
- Resources this task must resolve/prove:
- Introduced resource IDs:
- Actor capability keys this task must prove:
- Animation profiles this task must prove:
- Whether this task introduces a new actor action/animation (`animation_delta`):
- Resource/actor contract validator output:
- Validator output SHA256:

Rules:
- No resource may enter production without a valid collection method/tool/action.
- Human helpers/survivors require role-distinct work/combat animations.
- Animals may not use human-tool fallbacks.
- All seven pets require real species-specific attacks plus useful specialties; support-only fox/owl cannot pass.
- T44-T52 must register every newly introduced biome resource before `INTEGRATION_READY`.
- C5 is mandatory for T09/T16/T19/T21/T23 and all seven pet attacks. In T44–T52, new actions or evaluated resource profiles require regional contact/use-state review even with approved clip reuse; `animation_delta=false` cannot waive it.
- The already assigned T05 frozen scope is not expanded by this forward standard.

Run:
`python3 tools/havenline/production/resource_actor_contract.py --task TASK_ID --manifest <candidate-manifest> --output <proof.json>`

## Game Master owner-account contract
Mark REQUIRED or N/A from `GAME_MASTER_POLICY.json`.

When REQUIRED, record:
- `GAME_MASTER_POLICY.json` SHA256:
- Required proof flags for this task:
- Proof flags actually satisfied:
- Owner-slot binding count when T43/T70 applies:
- Server-side binding proof hash when T43/T70 applies:
- Game Master contract validator output:
- Validator output SHA256:

Forward rules:
- Exactly two owner Game Master slots exist; personal account identifiers stay outside public source.
- T43 binds the two designated owner accounts using verified Google Sign-In identity and must prove the exact shipping package + release-signing OAuth configuration.
- `GAME_MASTER` is permanent, owner-only and above public max VIP while inheriting every public VIP perk at maximum value.
- Every approved shop SKU is zero-cost for Game Master accounts; the Game Master claim path does not invoke real-money checkout and does not change normal-player prices.
- T13 implements `GM_CHALLENGE`, an elevated role-selected difficulty profile that remains independent from VIP, purchases, shop claims and spend history.
- Game Master activity is isolated from normal F2P/revenue/purchase-fairness populations and normal public competitive ranking.
- Applicable tasks are T13, T33-T37, T41-T43, T64-T66 and T70 as defined by `GAME_MASTER_POLICY.json`.
- This contract is forward-only and does not reopen T01-T08.

Run:
`python3 tools/havenline/production/game_master_contract.py --task TASK_ID --manifest <candidate-manifest> --output <proof.json>`

## Required tests
- Universal baseline:
- Task-specific:
- Approved-task regressions:
- Save-state matrix cases:
- Device/layout cases:
- Performance metrics:
- Resource/tool/actor contract validation where applicable:
- Game Master policy/contract validation where applicable:
- Reference-style material lock validation where material-affecting visual paths are changed (always for T70):

## Required evidence
- Exact candidate commit/hash.
- Changed-file manifest and base commit.
- Front/rear/left/right/3/4 where visually applicable.
- Gameplay scale.
- Close-up/detail.
- Relevant overhead.
- Relevant day/night/weather.
- Native 3840×2160 scale-1 where applicable.
- Motion cycles/transitions/contact/clipping where applicable.
- Resource/tool contact, impact timing and carry/delivery states where applicable.
- Human helper/survivor distinct-motion proof where applicable.
- Species-specific pet locomotion/attack/work proof where applicable.
- Google identity/recovery and Game Master entitlement/difficulty/fairness evidence where applicable.
- Logs, performance records and persistence records.
- Raw critic inputs and outputs.
- For any material-affecting candidate: exact changed-visual-path inventory, material inventory, actual A/B reference-pixel comparison, supplemental reference comparison where useful, style-lock validator proof, and C1 `reference_fidelity=10.0` plus `visual_language=10.0`.

## Required critics
List exact critic IDs from `CRITIC_MATRIX.json` plus any automatic C5 requirement added by the resource/actor contract. Any material-affecting visual change automatically adds C1 even when the task archetype would not otherwise require it.

-

Independent-required critics must use a genuinely separate reviewer/model
runtime. Builder self-review is recorded separately and cannot satisfy them.

## Performance budget
- Assigned subsystem budget:
- Baseline measurements:
- Candidate measurements:
- Remaining headroom:

## Candidate handoff
- Candidate commit:
- Candidate artifact hash:
- Evidence package:
- Resource/actor contract proof:
- Game Master contract proof:
- Reference-style lock proof:
- Known failures:
- Unresolved mandatory defects:
- Reconcile/rebase status against current integration head:
- Integration-owner disposition:

## Current reference acceptance packet

- Freeze the controlling primary video moments, selected GitHub render commit/path/hash and explicit owner-approved adaptations for each requirement.
- Name every mandatory view, use state, dimension and additional reference-sensitive dimension before review. Apply the union of graph/matrix/resource/action/style critic requirements; include C5 for the tasks and actions named in `REFERENCE_ACCEPTANCE_POLICY.json`.
- Bind the exact candidate and current policy with `reference_acceptance.acceptance_binding()`; retain each independent raw review and evidence hash.
- Record named deviations, responsible repair owner and retest evidence. Unobserved reference details stay labeled as authored decisions.
- Use the actual in-game camera and meaningful multi-angle details, full cycles/transitions for motion, playback/listening for temporal/audio claims, and required device evidence.
- A static render/archive score, partial clip, stale review, average or interim score cannot close this task. Final approval follows `REFERENCE_ACCEPTANCE_STANDARD.md` and preserves all stronger exact-10 requirements.
