# T12 activation handoff — execute only after T10 and T11 are APPROVED/integrated

**Current status:** preparation only. This document is an execution handoff, not permission to start shipping T12 runtime/data before dependencies close.

## 0. Non-negotiable entry conditions

All of the following must be true on the authoritative integration branch before T12 activation:

- T07 = APPROVED.
- T08 = APPROVED.
- T10 = APPROVED and integrated, with accepted completion record present.
- T11 = APPROVED and integrated, with accepted completion record present.
- T10/T11 are no longer active path owners.
- Exact checked-out HEAD is the intended post-T11 integration base.
- No T12 owned-path collision exists.
- `HavenlineGodot/scripts/progression_architecture.gd`, `HavenlineGodot/data/progression_levels_v1.json`, `HavenlineGodot/data/progression_milestones_v1.json`, and `HavenlineGodot/data/progression_bindings_v1.json` still do not exist before activation.

If any condition is false, T12 stays locked.

## 1. Reconcile exact accepted T10/T11 public IDs

Create an activation-time working file from the unresolved template:

```bash
cp Docs/Production/T12/BINDING_RESOLUTION_TEMPLATE.json Docs/Production/T12/BINDING_RESOLUTION.json
```

Populate only repository-proven accepted identifiers:

- set T10/T11 `accepted_integrated_source` to the exact accepted integrated commit;
- keep the accepted completion-record path;
- add each T12-consumed public ID with semantic `kind`, repository `source_path`, and exact RFC6901 JSON pointer;
- set `status` to `RESOLVED_FOR_ACTIVATION` and `promotion_allowed` to `true` only after all required bindings are present.

Then require a full-history checkout and bind the proof to the exact post-T11 activation head:

```bash
BASE="$(git rev-parse HEAD)"
test "$(git rev-parse --is-shallow-repository)" = "false"
python tools/havenline/task12/verify_binding_resolution.py \
  --resolution Docs/Production/T12/BINDING_RESOLUTION.json \
  --require-resolved \
  --activation-head "$BASE"
```

Any missing, provisional, example, debug, test-only, ambiguous or pointer-unproven identifier blocks activation.

## 2. Revalidate T12-owned preparation contracts

Run all dependency-independent preparation checks again on the exact activation base:

```bash
python tools/havenline/task12/prepare_activation.py
python tools/havenline/task12/validate_level_matrix.py
python tools/havenline/task12/validate_authoring_blueprint.py
python tools/havenline/task12/validate_fact_slot_binding_index.py
python tools/havenline/task12/materialize_progression_data.py
python tools/havenline/task12/reference_progression_oracle.py --input Docs/Production/T12/FULL_ENGINE_VECTOR_CORPUS.json
python tools/havenline/task12/validate_reference_runtime_semantics.py
python tools/havenline/task12/validate_runtime_interface.py
python tools/havenline/task12/validate_traceability.py
python tools/havenline/task12/validate_downstream_contract.py
python tools/havenline/task12/validate_data_schema.py
python tools/havenline/task12/reference_progression_oracle.py
python tools/havenline/task12/validate_candidate_evidence.py
python tools/havenline/task12/validate_critic_review_records.py
python tools/havenline/task12/validate_evidence_index.py
python tools/havenline/task12/fuzz_progression_contract.py
python tools/havenline/task12/benchmark_prebuild_validators.py
python -m unittest discover -s tools/havenline/task12/tests -p 'test_*.py' -v
```

`LEVEL_1_100_MATRIX.json`, `AUTHORING_BLUEPRINT.json`, `BINDING_SLOT_CATALOG.json`, and `FACT_SLOT_BINDING_INDEX_TEMPLATE.json` remain preparation inputs only. They must never be renamed/copied directly into shipping data. The materializer dry run must produce 100 levels + 10 milestones and PASS the real shipping validator without writing repository files.

## 3. Run the fail-closed activation preflight

```bash
BASE="$(git rev-parse HEAD)"
python tools/havenline/task12/prepare_activation.py --activate --base "$BASE"
```

Require `passed: true`. The preflight must independently verify dependency status, completed-task records, stale-owner closure, Level 1–100 matrix validity, exact T10/T11 binding resolution and path ownership safety.

## 4. Create the empty builder branch at the exact activation base

V3.2 assignment requires exact remote builder/integration lineage before `ASSIGNED`. Create the builder branch **before** assignment, from the exact activation base, but do not add runtime/data:

```bash
git branch havenline/T12-progression-architecture "$BASE"
git push origin havenline/T12-progression-architecture
```

Require the remote builder tip and remote integration tip to both equal `$BASE` before continuing. Do not reuse a governance-prep branch.

## 5. Integration owner stages reservation/PREPARED state, then V3.2 assigns T12

Use only the reservation patch emitted by the activation preflight. In one integration-owner assignment change:

1. stage the `@reservation:T12` alias in `PATH_OWNERSHIP.json`;
2. register the T12 workstream as `PREPARED` with the legacy workstream helper **only for PREPARED registration**;
3. run the V3.2 assignment authority for the real `ASSIGNED` transition.

```bash
python3 tools/havenline/production/workstream.py claim T12 \
  --owner progression-architecture-builder \
  --branch havenline/T12-progression-architecture \
  --base "$BASE" \
  --owned-alias @reservation:T12 \
  --status PREPARED

BUILDER_HEAD="$(git ls-remote origin refs/heads/havenline/T12-progression-architecture | awk '{print $1}')"
INTEGRATION_HEAD="$(git ls-remote origin refs/heads/codex/havenline-sequential-task-01 | awk '{print $1}')"
test "$BUILDER_HEAD" = "$BASE"
test "$INTEGRATION_HEAD" = "$BASE"

python3 tools/havenline/production/v32_assignment_claim.py T12 \
  --owner progression-architecture-builder \
  --branch havenline/T12-progression-architecture \
  --base "$BASE" \
  --owned-alias @reservation:T12 \
  --builder-head "$BUILDER_HEAD" \
  --integration-head "$INTEGRATION_HEAD"
```

For T11–T70, **never use `workstream.py claim --status ASSIGNED`**. V3.2 must write the assignment authority across `WORKSTREAM_REGISTRY.json`, `DEPENDENCY_GRAPH.json`, `PATH_OWNERSHIP.json` and `task-gates.json`, retaining `assignment_integration_commit`, `assignment_branch_head` and `assignment_lineage_state=SYNCHRONIZED`.

Merge the integration-owner assignment change only after production governance passes.

## 6. Synchronize the claimed builder branch before any shipping write

After the assignment governance commit lands, fast-forward/synchronize the still-empty builder branch to that integration commit before adding T12-owned files. The recorded assignment integration/head fields remain immutable provenance; this synchronization merely gives the builder checkout the authoritative ASSIGNED registry/ownership state.

Candidate/branch guards must recognize the active T12 owner/reservation before runtime/data work begins.

At this point—and not before—materializer write mode becomes eligible. On the synchronized claimed builder branch, require the resolved binding proof and original activation base `$BASE`:

```bash
cp Docs/Production/T12/FACT_SLOT_BINDING_INDEX_TEMPLATE.json /tmp/t12-resolved-fact-slots.json
# Populate every resolved_binding with either RESOLVED or allowed DEFERRED_LATER_OWNER.
# Levels 3, 4, 6, 9 and 10 are activation-critical opening slots: they MUST be RESOLVED.
# Those five rows must collectively consume at least one accepted T10 fact and at least one accepted T11 fact.
python tools/havenline/task12/validate_fact_slot_binding_index.py \
  --input /tmp/t12-resolved-fact-slots.json \
  --require-resolved
python tools/havenline/task12/materialize_progression_data.py \
  --write-shipping \
  --activation-base "$BASE" \
  --binding-resolution Docs/Production/T12/BINDING_RESOLUTION.json \
  --binding-index /tmp/t12-resolved-fact-slots.json
```

The tool must refuse writes unless T12 is the active claimed owner of `@reservation:T12`, the actual checkout is `havenline/T12-progression-architecture`, the recorded base matches `$BASE`, the binding proof resolves against `$BASE`, and the three shipping data files do not already exist.

## 7. Shipping implementation order

Use this order to reduce rework:

1. Build a temporary resolved fact-slot index from `FACT_SLOT_BINDING_INDEX_TEMPLATE.json`. Every Level 2–100 entry must be explicitly `RESOLVED` or allowed `DEFERRED_LATER_OWNER`; no row may remain null.
2. Before materialization, verify Levels 3/4/6/9/10 are RESOLVED and the set includes accepted T10 and T11 source tasks. Then use the activation-gated materializer to seed all three canonical datasets: `progression_levels_v1.json`, `progression_milestones_v1.json`, and `progression_bindings_v1.json`. Level 1 has no fact gate; Levels 2–100 use exact matching `t12.fact.slot.NNN` IDs.
3. Validate the level/milestone pair and binding dataset before runtime implementation depends on them:
   `python tools/havenline/task12/validate_progression_contract.py --levels HavenlineGodot/data/progression_levels_v1.json --milestones HavenlineGodot/data/progression_milestones_v1.json`
   and
   `python tools/havenline/task12/validate_fact_slot_binding_index.py --input HavenlineGodot/data/progression_bindings_v1.json --shipping`.
4. Re-run the 398-vector full corpus against the future engine behavior, not only the nine smoke vectors.
5. Implement `progression_architecture.gd` against `RUNTIME_INTERFACE_CONTRACT.json`, including stable fact-slot resolution and deferred-later-owner locking.
6. Add `test_task12_progression_architecture.gd` for pure validation, reachability, idempotency, spend-blindness, recovery, fact-slot resolution and performance-bound behavior.
7. Add `test_task12_integration.gd` against exact accepted T07/T08/T10/T11 integration behavior and the resolved opening fact slots.
8. Add `capture_task12_progression.gd` only after functional behavior is stable.
9. Re-run all impacted T01–T11 regression after integration-owner wiring.

Shared shipping wiring such as `main.gd`, `simulation.gd` or canonical shared registries remains integration-owner work.

## 8. Mandatory implementation behavior

The builder must preserve all of these prepared guarantees:

- exactly 100 Level records, 1–100;
- practical progression at every level;
- stable T12 level/slot/fact-slot/completion-event/milestone identities;
- Level 1 has no required fact gate; Levels 2–100 each reference exactly one canonical matching `t12.fact.slot.NNN`;
- external producer IDs remain in the binding index and never appear directly in progression level data;
- deferred later-owner fact slots keep their levels locked without invalidating the 1–100 topology;
- visible progression at least within the frozen x3/x6/x9/x0 cadence unless an accepted in-band substitution remains equally strong;
- major milestone per ten-level band;
- deterministic prerequisite/reachability evaluation;
- spend-blind eligibility and no energy wall;
- duplicate authoritative facts are no-ops;
- already-emitted completion/milestone events never emit twice after replay/restore;
- no inventory mutation, transform commit, camp spawn/upgrade, T13 difficulty decision or global save-schema ownership;
- event-driven/indexed evaluation, not unchanged full-graph per-frame traversal.

## 8. Evidence and critic sequence

After isolated implementation passes mechanical tests:

1. capture exact activation base, candidate SHA, trusted integration head and canonical `workstream.py validate-candidate` changed-path proof;
2. produce exact-100/DAG/reachability/per-level-effect/cadence reports;
3. produce accepted upstream binding audit;
4. produce deterministic replay/idempotency/reconstruction proof;
5. produce spend-blind input audit;
6. record cold-load, fact-evaluation, unlock-query, duplicate-replay, retained-growth and unchanged-frame performance evidence;
7. capture player-readable progression/milestone evidence where visual UI/world response applies;
8. run impacted T01–T11 regression on integrated candidate;
9. obtain C2, C3, C4, C7 independent review and C6 quantitative review against the exact current artifact;
10. run `final_candidate_gate.py` from the exact candidate checkout so it revalidates split shipping data, accepted binding ancestry/blob identity, the live canonical candidate guard, evidence digests, parity, critic provenance and hashes;
11. fix/retest until every mandatory dimension is strictly >9.0 unrounded, target 10.0, with zero unresolved mandatory defects and G1–G14 PASS.

T12 is APPROVED only after the integrated exact source passes all required gates. Preparation artifacts do not count as runtime approval evidence.
