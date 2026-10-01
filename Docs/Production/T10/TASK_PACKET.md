# T10 task packet — World Transformation Framework

## Governance state

- **Parallel mode:** dependency-safe isolated build while T09 remains active.
- **Allowed isolated state now:** `BUILDING_ISOLATED`, progressing to `BUILT_PENDING_DEPENDENCY` once the isolated candidate passes its full dependency-independent gates.
- **Integration gate:** T05 + T08 + T09 must all be `APPROVED` on the authoritative integration branch before T10 may become `INTEGRATION_READY`.
- **Builder branch:** `havenline/T10-world-transformation`.
- **Owner:** `world-transformation-builder`.
- **Current isolated lineage:** built from the dependency-independent T10 checkpoint; this is not the final production integration base.
- **Required reconciliation base:** the exact integration commit that records T09 approval/integration.
- **Planned reservation:** `@reservation:T10` as defined in `FROZEN_SCOPE.md` and `ACTIVATION_CHECKLIST.json`.
- **Evidence path after integration activation:** `Docs/Production/Evidence/T10/`.
- **Required critics:** C1, C2, C3, C4, C6, C7.
- **Forward gate:** every mandatory dimension strictly `> 9.0` unrounded, target `10.0`, all applicable G1-G14 and impacted regression PASS, zero unresolved mandatory defects.

## Builder objective now

Finish the deterministic transformation engine and presentation adapter on the isolated T10 branch, with neutral T10 fixtures standing in for unresolved T09 production authority. The framework must support pure eligibility preview, exact resource cost validation, atomic exact-once commit, stable transaction identity, deterministic state transitions, readable presentation phases and component-level recovery data.

The isolated candidate may be fully built, stress-tested, captured and internally reviewed now. It must not edit T09/T08 runtime paths, must not claim the real T09 adapter is certified, and must not be integrated before dependency closure.

## Required source contract

### `world_transform.gd`

Owns deterministic domain behavior only:

1. load/validate registered recipe definitions;
2. expose current transform state;
3. evaluate a recipe without mutation;
4. return exact blocked reasons/missing costs/prerequisites;
5. commit with a caller-supplied stable transaction ID;
6. revalidate immediately before commit;
7. prepare an authoritative resource debit intent exactly once;
8. advance target state only after an accepted authoritative resource receipt;
9. fail closed if the transaction cannot complete atomically;
10. reject duplicate, stale, replayed or out-of-order commits;
11. publish a deterministic committed event/result;
12. export/import component state and bounded replay-protection identities without defining T14's global save format.

### `world_transform_view.gd`

Presentation only:

- maps domain state to before/ready/preview/committing/complete/blocked visuals;
- never changes resource counts, progression or transform state;
- avoids rebuilding unchanged visuals;
- exposes deterministic capture hooks for evidence;
- remains content-neutral so T11 can supply final camp presentation later.

### `world_transform_recipes.json`

The candidate fixture/registry format must include stable fields equivalent to:

- `recipe_id`
- `source_state`
- `target_state`
- `costs[] { resource_id, quantity }`
- `prerequisites[]`
- `progression_tags[]`
- `presentation_key`
- explicit reversible/inverse metadata only when reversible

Validation rejects duplicate IDs, zero/negative costs, missing states, self-transitions unless explicitly modeled, nondeterministic duplicate cost rows, impossible inverse declarations and malformed prerequisites.

## Mandatory isolated test matrix — allowed before T09 approval

### Domain tests

- deterministic recipe parsing and ordering;
- duplicate/malformed recipe rejection;
- pure preview repeated many times with byte-for-byte identical state/resources;
- ready preview with exact cost summary;
- blocked preview with exact missing resource/prerequisite reasons;
- one valid fixture-authority commit advances exactly one state after exact accepted debit receipt;
- duplicate transaction ID is idempotent and does not debit twice;
- different transaction ID against stale source state fails without debit;
- failed authoritative debit leaves transform state unchanged;
- out-of-order transition rejected;
- forbidden skip/downgrade rejected;
- explicitly reversible fixture follows declared inverse rules only;
- export/import/replay preserves transform state and duplicate protection;
- malformed imported state fails closed;
- many recipe registrations and preview/commit bursts remain bounded;
- completed receipt history remains bounded rather than growing with lifetime transactions.

### Fixture integration tests before T09 approval

- fixture authority uses T10's request-scoped idempotency key;
- same-target concurrent request is rejected before any second debit;
- exact resource debit happens once and retries are idempotent;
- unsolicited well-formed receipts are rejected;
- stale resource availability can fail without premature world advancement;
- pending transaction can later succeed when authoritative resources recover;
- crash after debit / before T10 receipt acceptance recovers without second debit;
- different targets may be in flight concurrently and receipts may arrive out of order;
- component import rejects impossible multiple in-flight or duplicate retained receipt state;
- neutral R11 presentation remains presentation-only and bounded.

### Visual/capture evidence before T09 approval

- neutral fixture: blocked before enough resources;
- ready/preview after fixture resources are available;
- committing transition;
- completed target state;
- replay/duplicate attempt visibly leaves completed state unchanged and does not charge again;
- front/three-quarter plus other meaningful neutral-fixture views where applicable;
- adaptive phone/tablet/foldable layouts from the authoritative device matrix;
- event/performance traces tied to exact candidate source.

## Additional real-integration tests after T09 approval

These are the remaining dependency-bound tests required before `INTEGRATION_READY`:

- T08 delivered resource balance is the quantity used for transform affordability;
- resources harvested by T09 do not count until their authoritative acquisition/delivery path has committed;
- transform commit consumes exactly the integrated T08 authoritative amount once;
- carrying/stockpile presentation and simulation remain conserved after transform debit;
- T07 controls remain unchanged; no new required button/menu interaction;
- approved T01-T09 regression remains clean;
- T11 can consume the public transform interface without modifying transaction semantics;
- stale isolated fixture assumptions are removed or reconciled against the real T09/T08 adapter.

## Acceptance dimensions by critic

- **C1 Reference Fidelity:** transformation cadence/visual language remains faithful to the authoritative Havenline reference behavior without claiming unfinished T11 visual fidelity.
- **C2 Technical / Visual Integrity:** no geometry/contact/seam/clipping defects in neutral fixture presentation; cross-view state agrees.
- **C3 Havenline Gameplay Identity:** transformation is an automatic consequence of contextual physical play, not a new control-heavy or inventory-menu game.
- **C4 Gameplay UX / Readability:** blocked reason, readiness, cost, world change and next action are readable and truthful.
- **C6 Performance:** recipe evaluation, events, history/idempotency data and presentation updates remain bounded within published budgets.
- **C7 Progression / Difficulty:** state graph does not permit skips, impossible spikes caused by transform rules or meaningless duplicate states; later progression content can vary costs without changing framework semantics.

## Protected boundaries

Do not edit from the T10 builder branch unless an approved structured ChangeRequest authorizes it:

- T09-owned harvesting paths;
- T08 runtime modules;
- `HavenlineGodot/scripts/main.gd`;
- `HavenlineGodot/scripts/simulation.gd`;
- canonical shared registries owned by integration;
- approved T01-T09 content/assets;
- T11 final camp assets/content;
- T12/T13 progression/difficulty systems;
- T14 global persistence/versioning implementation.

## Parallel isolated work allowed before T09 approval

The following may be completed now without violating dependency semantics:

- all T10 runtime/domain source inside the frozen reservation;
- all T10 presentation source inside the frozen reservation;
- neutral recipe fixtures and content-neutral assets;
- domain, adversarial, fixture-integration and recovery tests;
- deterministic capture harnesses and device-layout evidence;
- performance/history/stress testing;
- source-contract validators and CI gates;
- internal repair loops and exact-source evidence packages;
- state advancement through `BUILDING_ISOLATED` to `BUILT_PENDING_DEPENDENCY`.

The following remain blocked until T09 is APPROVED/integrated:

- claiming the fixture authority as the real T09 adapter;
- editing T09/T08/integration-owned runtime paths;
- reconciling onto the exact final production integration base;
- becoming `INTEGRATION_READY`;
- merging/integrating T10 into the production integration branch;
- final production approval.

## Dependency handoff to integration

After T09 is integrated and marked APPROVED:

1. capture the exact new integration head;
2. run the strict activation/reconciliation preflight;
3. register/confirm `@reservation:T10` and the T10 owner through the integration owner;
4. reconcile `havenline/T10-world-transformation` onto that exact head;
5. replace/bind `FakeSimulationAuthority` fixture assumptions to the real approved T09/T08 authority interfaces;
6. rerun the formal T10 domain + real integration suites and impacted T01-T09 regression;
7. recapture affected evidence and run required C1/C2/C3/C4/C6/C7 reviews;
8. only then promote from `BUILT_PENDING_DEPENDENCY` to `INTEGRATION_READY` and enter controlled integration.

See `ACTIVATION_CHECKLIST.json` and `tools/havenline/task10/prepare_activation.py`.
