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

## Required tests
- Universal baseline:
- Task-specific:
- Approved-task regressions:
- Save-state matrix cases:
- Device/layout cases:
- Performance metrics:

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
- Logs, performance records and persistence records.
- Raw critic inputs and outputs.

## Required critics
List exact critic IDs from `CRITIC_MATRIX.json`.

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
- Known failures:
- Unresolved mandatory defects:
- Reconcile/rebase status against current integration head:
- Integration-owner disposition:
