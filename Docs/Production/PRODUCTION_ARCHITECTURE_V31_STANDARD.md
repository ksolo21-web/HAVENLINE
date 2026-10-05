# HAVENLINE Production Architecture V3.1 — Factory Hardening

## Purpose

V3.1 extends the verified V3 production-intelligence layer without changing gameplay, critic thresholds, or task ownership. It makes the production factory measurable, reproducible, resumable, self-checking, and explicit about proof invalidation.

This revision keeps the architecture at **V3.1** while closing the remaining passive-control gaps. The original eight systems remain authoritative, but the factory must now produce and consume their evidence automatically at terminal failure and forward closeout boundaries rather than relying on a builder to remember optional commands.

## Eight mandatory systems

1. **Persistent flake intelligence** — repeated pass/fail observations for the same exact source/gate/test/environment are classified historically. Flakiness never waives a mandatory gate; it changes diagnosis and retry routing only. Exact-environment observations come from immutable factory-observation bundles. If runner provenance is missing or ambiguous, flake classification is suppressed rather than guessed.
2. **Pipeline telemetry** — queue time, runtime, per-gate duration, reruns, C0 cycles, proof-cache hits, artifact size, and terminal stage are recorded without secrets. Terminal run telemetry is emitted in the same immutable factory-observation bundle and may optimize throughput only; it cannot alter acceptance quality.
3. **CI/toolchain reproducibility lock** — active production-critical GitHub Actions use exact commit SHAs and Node-24-native action runtimes; runner image family and runtime image metadata are recorded; engines/templates/tool versions remain checksum/version pinned. Closed historical workflows may be explicitly retired/frozen instead of rewritten, but may not silently re-enter forward execution. The independent reviewer runtime is repository-hash-pinned, cache-first, and must verify a valid cache without network access.
4. **Tiered evidence retention** — ephemeral raw evidence is separated from durable approval manifests and irreplaceable evidence. Approval provenance must survive artifact expiry. Forward closeout evidence must include the terminal factory-observation record in addition to task-specific approval evidence.
5. **Runtime-observed dependency learning** — observed runtime/resource/signal dependencies may add regression coverage. Only source-bound runtime dependency traces tied to the exact candidate may enter the observation stream. Learned observations never silently remove static mandatory coverage.
6. **Canonical task-state snapshots** — an active task has one machine-readable derived state containing exact source/base, lifecycle, last verified gate, blockers, V3 readiness, contracts, and next executable action. The factory observer emits the terminal derived snapshot, but lifecycle authority remains the canonical registries/workstream state.
7. **Mutation/canary validation** — deliberately broken synthetic inputs must continue to be rejected by critical validators. A validator that cannot reject its canary is itself broken.
8. **Transitive proof invalidation** — reopening an approved task/contract explicitly identifies downstream tasks and proof families that become stale. Contract registry changes are detected from the actual base→head diff, including removals, and automatically generate a conservative invalidation forecast. Reuse is blocked for invalidated proof until regenerated or explicitly revalidated.

## Automatic factory observation

`tools/havenline/production/factory_observer.py` is the canonical terminal-run observation producer. From immutable GitHub run/job/artifact records it emits:

- `factory-observation.json`
- a pipeline telemetry record
- exact-environment flake observations when provenance is complete
- a derived task-state snapshot when the task can be resolved
- validated exact-source runtime dependency traces when present

The observation bundle is **evidence, not authority**. It may not approve a task, change lifecycle state, lower thresholds, waive a mandatory gate, or replace C0/C1–C11.

Terminal failures routed through C0 must preserve the factory observation automatically. T10+ successful/approval closeout must preserve an exact-source terminal factory observation and pass `factory_closeout_gate.py` before approval.

## Forward closeout enforcement

For T10–T70, the forward closeout runner must include:

- `factory_observer.py`
- `factory_closeout_gate.py`
- `closure_validator.py`
- `evidence_retention.py`
- `task_state_snapshot.py`

The factory closeout gate fails closed when the observation is missing, source/task identity differs, terminal disposition is not successful, runner provenance is not exact, telemetry is invalid, task-state evidence is invalid, or runtime dependency traces are malformed/stale.

T09 and earlier completed approvals are not retroactively rewritten merely to adopt V3.1. Their accepted evidence remains frozen unless those tasks are explicitly reopened.

## Automatic proof invalidation

`proof_invalidation.py diff --base <BASE> --head <HEAD>` compares the actual versioned contract registry across source boundaries. For every changed or removed contract it derives affected task roots, descendants, proof families, and reusable gate-index records. A detected change sets `proof_reuse_blocked=true` and requires integration-owner disposition; it never automatically revokes a prior approval.

## CI/runtime lifecycle policy

- Active critical workflows must use exact Node-24-native action SHAs from `CI_TOOLCHAIN_LOCK.json`.
- Mutable action tags remain forbidden.
- A toolchain-lock change requires a fresh hosted governance pass.
- Retired workflows are listed explicitly and must be fail-closed for forward use.
- Reviewer model/runtime files are validated against repository-pinned SHA-256 identities.
- A verified reviewer cache is the primary path and must require zero publisher/network access.
- Network retrieval is recovery-only for a missing/invalid exact pinned cache and must still hash-verify all bytes.

## Safety rules

- V3.1 is governance/tooling only unless an active task separately authorizes runtime work.
- Flake classification cannot convert FAIL to PASS.
- Telemetry cannot be used to lower quality thresholds for speed.
- Factory observations cannot mutate lifecycle state or grant approval.
- Learned runtime dependencies are additive by default; static coverage remains authoritative.
- Approval/critic/physical/integration proof remains exact-source where V3 already requires it.
- Task-state snapshots are derived records, not an alternate lifecycle authority.
- Mutation canaries never touch shipping runtime or player saves.
- Proof invalidation is conservative: uncertainty invalidates rather than preserves proof.
- CI lock updates require explicit governance review and a new hosted validation source.
- No active V3.1 migration may modify `HavenlineGodot/` gameplay/runtime merely to satisfy architecture validation.

## Acceptance

V3.1 passes only when all eight systems and their automatic-consumption contracts validate in hosted governance together with V2, V3, C0, C1–C11 readiness, path ownership, packet generation, forward closeout wiring, factory-observer consumption, contract-diff invalidation, and integration-scope validation.

The same frozen source used for final V3.1 acceptance must also prove the independent critic runtime can restore/verify its exact cache and execute successfully under the locked active CI toolchain. No `HavenlineGodot/` gameplay/runtime file may be changed merely to make V3.1 pass.
