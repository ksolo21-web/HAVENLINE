# T10 task packet — World Transformation Framework

## Governance state

- **Preparation mode:** dependency-safe parallel prep while T09 remains active.
- **Production status target now:** `PREPARED`, not `ASSIGNED`.
- **Production implementation gate:** T05 + T08 + T09 must all be `APPROVED` on the authoritative integration branch.
- **Prepared branch:** `havenline/governance-t10-prep`.
- **Future isolated builder branch:** `havenline/T10-world-transformation`.
- **Future owner:** `world-transformation-builder`.
- **Activation base:** the exact integration commit that records T09 approval/integration, not the current pre-T09-completion checkpoint.
- **Planned reservation:** `@reservation:T10` as defined in `FROZEN_SCOPE.md` and `ACTIVATION_CHECKLIST.json`.
- **Evidence path after activation:** `Docs/Production/Evidence/T10/`.
- **Required critics:** C1, C2, C3, C4, C6, C7.
- **Forward gate:** every mandatory dimension strictly `> 9.0` unrounded, target `10.0`, all applicable G1-G14 and impacted regression PASS, zero unresolved mandatory defects.

## Builder objective after activation

Implement a small, deterministic transformation engine and presentation adapter that later content can use without duplicating transaction logic. The framework must support pure eligibility preview, exact resource cost validation, atomic exact-once commit, stable transaction identity, deterministic state transitions, readable presentation phases and component-level recovery data.

The first candidate must prove the framework with neutral T10-owned fixtures. It must not ship final T11 camp buildings or pretend T11 content is complete.

## Required source contract

### `world_transform.gd`

Owns deterministic domain behavior only:

1. load/validate registered recipe definitions;
2. expose current transform state;
3. evaluate a recipe without mutation;
4. return exact blocked reasons/missing costs/prerequisites;
5. commit with a caller-supplied stable transaction ID;
6. revalidate immediately before commit;
7. debit through the published authoritative resource interface once;
8. apply target state once;
9. roll back/fail closed if the transaction cannot complete atomically;
10. reject duplicate, stale, replayed or out-of-order commits;
11. publish a deterministic committed event/result;
12. export/import component state and applied transaction identities without defining T14's global save format.

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

## Mandatory test matrix

### Domain tests

- deterministic recipe parsing and ordering;
- duplicate/malformed recipe rejection;
- pure preview repeated many times with byte-for-byte identical state/resources;
- ready preview with exact cost summary;
- blocked preview with exact missing resource/prerequisite reasons;
- one valid commit debits exact cost and advances exactly one state;
- duplicate transaction ID is idempotent and does not debit twice;
- different transaction ID against stale source state fails without debit;
- failed resource debit or failed state application leaves pre-transaction state intact;
- out-of-order transition rejected;
- forbidden skip/downgrade rejected;
- explicitly reversible fixture follows declared inverse rules only;
- export/import/replay preserves transform state and duplicate protection;
- malformed imported state fails closed;
- many recipe registrations and preview/commit bursts remain bounded.

### Integration tests after T09 approval

- T08 delivered resource balance is the quantity used for transform affordability;
- resources harvested by T09 do not count until their authoritative acquisition/delivery path has committed;
- transform commit consumes exactly the T08 authoritative amount once;
- carrying/stockpile presentation and simulation remain conserved after transform debit;
- T07 controls remain unchanged; no new required button/menu interaction;
- approved T01-T09 regression remains clean;
- T11 can consume the public transform interface without modifying transaction semantics.

### Visual/capture evidence

- neutral fixture: blocked before enough resources;
- ready/preview after resources are available;
- committing transition;
- completed target state;
- replay/duplicate attempt visibly leaves completed state unchanged and does not charge again;
- front/side/three-quarter/overhead/gameplay/detail where applicable;
- adaptive phone/tablet/foldable layouts;
- native 3840x2160 scale-1 evidence where applicable;
- event/performance traces tied to exact candidate source.

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

## Parallel-prep work allowed before T09 approval

The following may be completed now without violating dependency semantics:

- freeze this scope and task packet;
- define the future disjoint ownership reservation;
- define validator/test/capture acceptance contracts;
- prepare CI workflow scaffolding;
- prepare one-command activation tooling that refuses to activate until all dependencies are actually approved;
- static/internal review of the packet for T09/T11/T14 scope collisions.

No T10 production runtime source may be claimed as an integration candidate before T09 is approved.

## Activation handoff

After T09 is integrated and marked APPROVED, run the activation preflight from this packet against the exact new integration head. It must refuse stale or incomplete dependency state. Then reserve `@reservation:T10`, register/claim T10 as ASSIGNED, cut `havenline/T10-world-transformation` from that exact post-T09 integration checkpoint, run registry validation and begin the isolated builder loop.

See `ACTIVATION_CHECKLIST.json` and `tools/havenline/task10/prepare_activation.py`.
