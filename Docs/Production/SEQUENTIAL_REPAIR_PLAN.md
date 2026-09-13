# Havenline — authoritative controlled integration plan

This file is the forward operational companion to `HAVENLINE_BUILD_PLAN_V2.md`.

The exact pre-migration sequential plan is preserved byte-for-byte at
`Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md`
with provenance in the adjacent JSON record. V2 replaces pure serial building
with dependency-controlled parallel construction, while retaining serial,
integration-owner-controlled production integration.

## Current authoritative checkpoint

- Integration branch: `codex/havenline-sequential-task-01`.
- T01: APPROVED at `45ba7905cd468c229cd61364f4d1ac45b14d3e5e`.
- T02: APPROVED at `1f0ba3bede3d160a34751c2fcdbfa78c1b6785ff`.
- T03: APPROVED at accepted gameplay source
  `5df9726e0b1c33f0f8865385b1c49aca229fd461`; verified closure is recorded in
  `Docs/Production/T03/verified-completion.json`.
- T04: ASSIGNED on isolated branch `havenline/T04-camera` from integration base
  `5135cddf96123afb962f4046f41e5ac0e510428a`.
- T05+ runtime production remains LOCKED until separately prepared and assigned.

## Forward acceptance rule

For every not-yet-approved task, PASS requires:

1. every applicable mandatory reviewed dimension is **strictly greater than
   9.0, unrounded**;
2. every applicable gate G1-G14 passes;
3. every critic required by `CRITIC_MATRIX.json` has current complete evidence;
4. no unresolved mandatory defect remains;
5. integration-candidate regression passes after merge/reconciliation.

Target remains 10/10. T01/T02 remain approved under their historical accepted
records and are not retroactively revoked.

## Controlled production flow

`DEPENDENCY GRAPH -> PREPARE PACKET -> CLAIM DISJOINT PATHS -> BUILD ISOLATED
-> TEST -> PACKAGE CANDIDATE -> INTEGRATION OWNER REVIEW -> RECONCILE STALE BASE
-> INTEGRATE CLEANLY -> IMPACT-BASED REGRESSION -> FRESH INTEGRATION EVIDENCE
-> APPLICABLE CRITICS -> FIX/RETEST -> APPROVE -> UNLOCK DEPENDENTS`

Only the integration owner may move production changes onto the integration
branch. An isolated builder can reach `INTEGRATION_READY`; it cannot mark
itself `APPROVED`.

## States

`LOCKED`, `PREPARED`, `ASSIGNED`, `BUILDING_ISOLATED`,
`BUILT_PENDING_DEPENDENCY`, `INTEGRATION_READY`, `INTEGRATING`,
`UNDER_REVIEW`, `FIX_REQUIRED`, `APPROVED`, `BLOCKED`.

No state change is time-based.

## Collision protection

`PATH_OWNERSHIP.json` is authoritative for active ownership and protected
paths. No two active workstreams may own the same production path.

If a builder needs a foreign-owned or integration-only path, it creates a
change request under `Docs/Production/ChangeRequests/` and does not modify that
path. The integration owner resolves the request.

The current T03 is grandfathered as the final legacy task allowed to finish on
the integration branch because its runtime changes were already integrated
before V2. No T04+ builder receives that exception.

## Regression and evidence

Changed files are mapped through `REGRESSION_MATRIX.json`. The integration
candidate runs the union of universal checks and all impacted approved-task
checks. Unknown production changes fall back to the full mandatory suite set.

Evidence must be deterministic and exact-source-bound. Capture metadata records
candidate commit/hash, scene/state, camera, renderer, resolution, build/run id,
and timestamp. Visual tasks use front/rear/left/right/3/4/gameplay/detail/
overhead/condition/native-4K views where applicable. Motion tasks use complete
real-time/slow cycles plus turns, transitions and contact/clipping views.

`SAVE_STATE_MATRIX.json` and `DEVICE_LAYOUT_MATRIX.json` define early
persistence/device coverage. `PERFORMANCE_BUDGETS.json` defines headroom gates.
None of these early checks replace T68/T69 physical-device certification.

## Critic independence

C1-C11 and per-task applicability are defined in `CRITIC_MATRIX.json`.
Builder self-review, a second persona, or a second prompt from the same builder
is not an independent pass. When an independent runtime is required and no
separate $0 reviewer is available, useful construction/testing continues but
the critic gate remains `BLOCKED`. Never manufacture a pass and never add a
paid critic dependency.

## Wave 1 after T03 approval

T03 is approved. The registry may now assign these workstreams individually
after each packet and owner are prepared:

- `havenline/T04-camera` — T04 camera/composition (currently assigned).
- `havenline/T05-props` — T05 station/prop kit.
- `havenline/T06-character1` — T06 Character 1 motion.
- QA/integration infrastructure may continue separately.

Those workstreams are isolated and path-disjoint. Shared wiring remains
integration-owner work or a change request.

## Sequence

The release-critical task list is T01-T70 exactly as defined in
`HAVENLINE_BUILD_PLAN_V2.md` and `DEPENDENCY_GRAPH.json`. Numerical order is
the roadmap order; dependency approval, ownership and integration gates decide
what may build in parallel.

## Resumability

After every integration or failed gate, update:
`WORKSTREAM_REGISTRY.json`, `task-gates.json`, task evidence, exact candidate
hashes, tests, critic raw outputs, blockers and next executable action.

A governance/tooling commit does not approve gameplay. A task packet does not
approve gameplay. Only the integrated candidate satisfying all applicable
gates can become APPROVED.
