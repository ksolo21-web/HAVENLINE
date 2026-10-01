# HAVENLINE Production Architecture V3

## Purpose

V3 turns the existing controlled task pipeline into a production-intelligence system. V2/V2-forward remains authoritative for acceptance, path ownership, task states, critic independence, exact-source evidence and the strict >9.0 unrounded quality threshold. V3 does **not** weaken those controls. It adds the ability to decide what can start, what should start, what proof may be safely reused, whether a candidate is likely to integrate cleanly, whether cross-task contracts remain compatible, and whether a failure has already been diagnosed elsewhere.

The six P0 V3 systems are:

1. **Preactivation feasibility** — prove required local/external/hardware capabilities before runtime implementation.
2. **Critical-path/resource-aware scheduling** — rank safe work from the authoritative dependency graph and WIP/resource policy.
3. **Content-addressed gate fingerprints** — reuse logically identical deterministic proof without treating an unrelated SHA movement as a reason to rerun everything.
4. **Synthetic merge forecasting** — detect integration drift, path overlap and likely conflicts before the integration owner reaches the candidate.
5. **Versioned contract compatibility** — make cross-task interfaces explicit and fail breaking changes closed unless migration/revalidation is declared.
6. **Failure intelligence** — make C0 consult verified prior failures/repairs before diagnosing from scratch.

## Non-negotiable compatibility with existing architecture

- C0 remains non-voting.
- C1-C11 applicability and strict scoring are unchanged.
- A builder may not self-approve or self-integrate.
- `FIX_REQUIRED` still requires C0 + a bounded repair plan.
- Runtime ownership and ChangeRequest rules remain fail-closed.
- Physical certification cannot be replaced by CI/emulator/render evidence.
- A proof reuse decision never changes a failed result into a pass; it only avoids rerunning a gate when the complete gate-input fingerprint is identical and the reuse class permits it.
- `critic_review`, `integration`, `post_integration_regression`, `closeout`, `physical_device`, and `release_manifest` remain exact-source/fresh where required and are never silently inherited from another SHA.

## 1. Pre-activation feasibility

Machine authority:

- `Docs/Production/TASK_CAPABILITY_MATRIX.json`
- `Docs/Production/CAPABILITY_STATUS.json`
- `tools/havenline/production/preactivation_feasibility.py`

A task must not move from preparation into runtime implementation merely because dependencies are approved. Its resolved capability set must also be satisfiable.

Capability states:

- `READY` — requirement is currently verifiable.
- `UNVERIFIED` — external/manual prerequisite has not been proven; runtime activation is blocked if required now.
- `UNAVAILABLE` — prerequisite is known unavailable; activation is blocked.
- `DEFERRED` — prerequisite is intentionally later than the current phase and cannot be used to claim task readiness.
- `MISSING_LOCAL` — a repository/tooling prerequisite that should exist is absent.

Repository-local capabilities are probed from actual files/contracts. External capabilities are represented only by non-secret status records; credentials/tokens are never committed.

## 2. Critical path and WIP scheduling

Machine authority:

- `Docs/Production/PRODUCTION_SCHEDULER_POLICY.json`
- `tools/havenline/production/critical_path_scheduler.py`

The scheduler reads `DEPENDENCY_GRAPH.json`, V3 feasibility, forward execution mode, current registry state and configured capacity. It emits:

- `READY_NOW` — dependencies + packet + capabilities support activation.
- `PREP_ONLY` — useful preparation is safe, but runtime work must remain locked.
- `BLOCKED_CAPABILITY` — required capability is unavailable/unverified.
- `BLOCKED_DEPENDENCY` — prerequisite tasks remain unapproved.
- `INTEGRATION_QUEUE` — candidates already waiting for the single integration authority.

Priority is deterministic and transparent: downstream criticality, dependency depth, unblock value, readiness and current WIP constraints. The score is a scheduling heuristic, not an acceptance score.

The scheduler never grants ownership or approval. It recommends work; `workstream.py` and the dependency graph remain authoritative.

## 3. Content-addressed proof reuse

Machine authority:

- `Docs/Production/GATE_FINGERPRINT_POLICY.json`
- `Docs/Production/GATE_RESULT_INDEX.json`
- `tools/havenline/production/gate_fingerprint.py`

A gate fingerprint binds the gate to content that can materially affect its result:

- shipping runtime tree;
- task-owned adapter/tool tree;
- applicable gate runner/contract;
- forward/critic authorities;
- accepted dependency source identities;
- relevant toolchain/contract inputs.

Reuse classes:

- `deterministic_reusable` — equal fingerprint can reuse a prior deterministic PASS with preserved provenance.
- `rebind_with_provenance` — heavy generated evidence may reuse immutable bytes only after a new bridge record proves the new candidate has the same relevant input fingerprint.
- `exact_source_required` — no cross-SHA reuse. Run fresh.

A fingerprint mismatch invalidates reuse. Missing inputs fail closed. FAIL results are never converted into PASS through reuse.

## 4. Synthetic merge forecast

Machine authority:

- `tools/havenline/production/synthetic_merge_forecast.py`

For an isolated candidate and current integration head, the forecast computes:

- candidate branch point / merge base;
- candidate-changed paths;
- integration-drift paths;
- direct path overlap;
- merge-tree conflict signal when git supports it;
- governance-only versus production drift;
- likely affected approved tasks/change-impact consequences.

An `INTEGRATION_READY` candidate should be forecast whenever the integration head advances materially. A forecast is not integration and cannot replace post-integration regression.

## 5. Versioned compatibility contracts

Machine authority:

- `Docs/Production/CONTRACT_REGISTRY.json`
- `tools/havenline/production/contract_compatibility.py`

Cross-task interfaces are registered by owner, version, consumers, compatibility policy and migration requirement. Examples include inventory transfer, context/action identity, world transactions, persistence schema, progression, economy grants, backend authority, LiveOps payloads and region transitions.

Breaking contract changes require:

- an explicit version change;
- migration/compatibility notes;
- declared affected consumers;
- consumer revalidation before closure.

A task may not silently change a shared interface merely because its own local tests pass.

## 6. Cross-task failure intelligence

Machine authority:

- `Docs/Production/FAILURE_INTELLIGENCE.json`
- `tools/havenline/production/failure_intelligence.py`

Verified failure records contain:

- normalized fingerprint;
- classification;
- affected layer/object;
- observable signature;
- proven root cause;
- causal repair;
- protected files that must not be changed;
- proof that closed the issue;
- prevention rule;
- source defect-ledger reference.

C0 queries this knowledge base before model diagnosis. A historical match is advisory evidence, never permission to assume the same cause. C0 must compare the current run evidence and explicitly confirm or reject the match.

## Activation decision

For T10+, the V3 activation decision is:

`DEPENDENCIES -> PACKET/SCOPE -> OWNERSHIP RESERVATION -> V3 FEASIBILITY -> FORWARD PLAN -> CAPACITY/WIP -> START BUILD`

A task can be prepared before its dependencies finish, but runtime build activation requires the authoritative state to satisfy the above checks.

## Failure decision

`TERMINAL FAILURE -> NORMALIZE FINGERPRINT -> QUERY FAILURE INTELLIGENCE -> C0 COMPLETE DIAGNOSIS -> BOUNDED REPAIR PLAN -> BUILDER -> CHEAP SENTINEL -> ONLY THEN EXPENSIVE FAN-OUT`

No builder repair may be justified only by a red status or historical similarity.

## Integration decision

`INTEGRATION_READY -> SYNTHETIC MERGE FORECAST -> CONTRACT COMPATIBILITY -> CURRENT CHANGE IMPACT -> INTEGRATION OWNER -> INTEGRATE -> FRESH POST-INTEGRATION REGRESSION/EVIDENCE`

A clean forecast does not waive fresh integrated validation.

## Architecture acceptance

V3 itself passes only when:

- all T10-T70 tasks resolve feasibility without schema gaps;
- every capability reference exists in the catalog;
- the scheduler processes the full dependency graph deterministically;
- all forward gates have a fingerprint reuse policy;
- exact-source-only gates cannot be reused across SHAs;
- merge forecasting is fail-closed on unknown refs/errors;
- all compatibility contracts have valid owners/consumers/versions;
- failure intelligence records validate and C0 can consume prior matches;
- forward task packets expose V3 readiness/commands;
- hosted governance validates all V3 controls on one exact source SHA.
