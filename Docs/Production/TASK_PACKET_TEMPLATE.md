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
- G13 SCORE (>9.0 unrounded in every mandatory dimension; target 10/10)
- G14 INTEGRATION

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
- Combat-capable animals require species-specific attack animations.
- T44-T52 must register every newly introduced biome resource before `INTEGRATION_READY`.
- C5 is additionally mandatory for T09/T16/T19/T21/T23 and for T44-T52 whenever `animation_delta=true`.
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

## Required critics
List exact critic IDs from `CRITIC_MATRIX.json` plus any automatic C5 requirement added by the resource/actor contract.

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
- Known failures:
- Unresolved mandatory defects:
- Reconcile/rebase status against current integration head:
- Integration-owner disposition:
