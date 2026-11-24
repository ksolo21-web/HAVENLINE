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
- T04: APPROVED at accepted gameplay source
  `e08fd37e9a999d878644c03089c4b4b253bd7472`; verified closure is recorded in
  `Docs/Production/T04/verified-completion.json`.
- T05: APPROVED at accepted gameplay source
  `fa6fa70f154f3757d22303522ca3f6de2c3d391f`; verified closure is recorded in
  `Docs/Production/T05/verified-completion.json` after 18 suites / 1119 checks,
  77 source-bound frames, strict C1+C2 PASS, C6 minimum 9.1, final pixel
  signoff and G1-G14.
- T06 is APPROVED at accepted isolated source
  `47f86fae25b099abb5c7096c37ca7495453b2b8f`, integrated at
  `91f35f331aaabe2b1785b10c0d911f20da6f12d9`; its verified closure is recorded
  in `Docs/Production/T06/verified-completion.json` after 19 suites / 1345
  checks, exact evidence identity, exhaustive motion/surface gates and required
  C1/C2/C5/C6 review.
- T07 is APPROVED at accepted isolated source
  `0a30dc0859541626eb6aa9a9bb749abc93dcb355`, integrated at
  `94b3f6c5097356a3857ebd13a77fb1e316eb06ae`; its verified closure is recorded
  in `Docs/Production/T07/verified-completion.json` after 21 suites / 1441
  checks and strict C2/C3/C4/C6/C11 review.
- T08 is APPROVED at exact integrated source
  `9d56ea8ae972d0a0705ff8b985e13fab31dde493`; its verified closure is recorded
  in `Docs/Production/T08/verified-completion.json` after 23 suites / 1535
  checks, all 44 locked frames and both locked recordings, G1-G14, and strict
  C2 9.55 / C3 9.48 / C4 9.52 / C6 9.61 independent review.
- T09 is ASSIGNED to `harvesting-acquisition-builder` on isolated branch
  `havenline/T09-harvesting` from exact integration base
  `7492074e40a0b061f31d8c32602b7a581b2610f3`; its frozen scope, task packet and
  disjoint path reservation are authoritative. T10+ remains LOCKED.

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

## Current wave after T08 approval

T03 is approved. The registry may now assign these workstreams individually
after each packet and owner are prepared:

- T04 camera/composition is complete and APPROVED.
- T05 station/prop kit is complete and APPROVED at `fa6fa70f154f3757d22303522ca3f6de2c3d391f`.
- T06 Character 1 motion/contact foundation is complete and APPROVED; preserve
  its accepted and integrated sources.
- T07 deterministic simple-control/context director is complete and APPROVED;
  preserve its accepted and integrated sources.
- T08 visible inventory, carrying and transfers is complete and APPROVED;
  preserve exact integrated source
  `9d56ea8ae972d0a0705ff8b985e13fab31dde493` and its verified closure.
- T09 harvesting and automatic acquisition is ASSIGNED to
  `harvesting-acquisition-builder` on isolated branch
  `havenline/T09-harvesting`; build and review against its frozen packet are
  next. T10+ remains LOCKED.
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
