# HAVENLINE Production Architecture V3.1 — Factory Hardening

## Purpose

V3.1 extends the verified V3 production-intelligence layer without changing gameplay, critic thresholds, or task ownership. It makes the production factory measurable, reproducible, resumable, self-checking, and explicit about proof invalidation.

## Eight mandatory systems

1. **Persistent flake intelligence** — repeated pass/fail observations for the same source/gate/test/environment are classified historically. Flakiness never waives a mandatory gate; it changes diagnosis and retry routing only.
2. **Pipeline telemetry** — queue time, runtime, per-gate duration, reruns, C0 cycles, proof-cache hits, artifact size, and terminal stage are recorded without secrets.
3. **CI/toolchain reproducibility lock** — production-critical actions use exact commit SHAs; runner image family and runtime image metadata are recorded; engines/templates/tool versions remain checksum/version pinned.
4. **Tiered evidence retention** — ephemeral raw evidence is separated from durable approval manifests and irreplaceable evidence. Approval provenance must survive artifact expiry.
5. **Runtime-observed dependency learning** — observed runtime/resource/signal dependencies may add regression coverage. Learned observations never silently remove static mandatory coverage.
6. **Canonical task-state snapshots** — an active task has one machine-readable state containing exact source/base, lifecycle, last verified gate, blockers, V3 readiness, contracts, and next executable action.
7. **Mutation/canary validation** — deliberately broken synthetic inputs must continue to be rejected by critical validators. A validator that cannot reject its canary is itself broken.
8. **Transitive proof invalidation** — reopening an approved task/contract explicitly identifies downstream tasks and proof families that become stale. Reuse is blocked for invalidated proof.

## Safety rules

- V3.1 is governance/tooling only unless an active task separately authorizes runtime work.
- Flake classification cannot convert FAIL to PASS.
- Telemetry cannot be used to lower quality thresholds for speed.
- Learned runtime dependencies are additive by default; static coverage remains authoritative.
- Approval/critic/physical/integration proof remains exact-source where V3 already requires it.
- Task-state snapshots are derived records, not an alternate lifecycle authority.
- Mutation canaries never touch shipping runtime or player saves.
- Proof invalidation is conservative: uncertainty invalidates rather than preserves proof.
- CI lock updates require explicit governance review and a new hosted validation source.

## Acceptance

V3.1 passes only when all eight systems validate in hosted governance together with V2, V3, C0, C1–C11 readiness, path ownership, packet generation, and integration-scope validation. No `HavenlineGodot/` gameplay/runtime file may be changed merely to make V3.1 pass.
