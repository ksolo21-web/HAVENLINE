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
- `HavenlineGodot/scripts/progression_architecture.gd`, `HavenlineGodot/data/progression_levels_v1.json`, and `HavenlineGodot/data/progression_milestones_v1.json` still do not exist before activation.

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

`LEVEL_1_100_MATRIX.json` remains preparation input only. It must never be renamed/copied directly into shipping data.

## 3. Run the fail-closed activation preflight

```bash
BASE="$(git rev-parse HEAD)"
python tools/havenline/task12/prepare_activation.py --activate --base "$BASE"
```

Require `passed: true`. The preflight must independently verify dependency status, completed-task records, stale-owner closure, Level 1–100 matrix validity, exact T10/T11 binding resolution and path ownership safety.

## 4. Integration owner reserves and activates T12

Use only the reservation patch emitted by the activation preflight. Apply `@reservation:T12` through the integration owner, then claim:

```bash
python3 tools/havenline/production/workstream.py claim T12 \
  --owner progression-architecture-builder \
  --branch havenline/T12-progression-architecture \
  --base "$BASE" \
  --owned-alias @reservation:T12 \
  --status ASSIGNED
```

Update dependency graph/task gates/workstream state consistently through the integration owner. Validate zero ownership collisions.

## 5. Create the isolated builder branch from the exact activated head

Create `havenline/T12-progression-architecture` only from the exact post-activation integration head. Do not reuse the governance-prep branch as the shipping builder branch.

Before adding runtime/data, candidate guard must recognize the active T12 owner/reservation.

## 6. Shipping implementation order

Use this order to reduce rework:

1. Author `progression_milestones_v1.json` from accepted T12 milestone IDs and reconciled bindings.
2. Author `progression_levels_v1.json` from the validated 100-level matrix, replacing abstract binding classes only with accepted resolved IDs/content-owner hooks.
3. Validate the two real shipping files together before runtime implementation depends on them:
   `python tools/havenline/task12/validate_progression_contract.py --levels HavenlineGodot/data/progression_levels_v1.json --milestones HavenlineGodot/data/progression_milestones_v1.json`.
4. Implement `progression_architecture.gd` against `RUNTIME_INTERFACE_CONTRACT.json`.
5. Add `test_task12_progression_architecture.gd` for pure validation, reachability, idempotency, spend-blindness, recovery and performance-bound behavior.
6. Add `test_task12_integration.gd` against exact accepted T07/T08/T10/T11 integration behavior.
7. Add `capture_task12_progression.gd` only after functional behavior is stable.
8. Re-run all impacted T01–T11 regression after integration-owner wiring.

Shared shipping wiring such as `main.gd`, `simulation.gd` or canonical shared registries remains integration-owner work.

## 7. Mandatory implementation behavior

The builder must preserve all of these prepared guarantees:

- exactly 100 Level records, 1–100;
- practical progression at every level;
- stable T12 level/slot/completion-event/milestone identities;
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
