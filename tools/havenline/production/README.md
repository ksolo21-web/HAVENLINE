# Havenline Production Accelerator — V2

This directory is the authoritative controlled-parallel production toolset. Each tool has one responsibility so builders and the integration owner cannot bypass path, dependency, evidence, regression, critic or closure gates through a broad self-certifying command.

Core tools:
- `task_packet.py` — generate/freeze the task packet from the dependency graph, registry, ownership and critic matrix.
- `workstream.py` — claim workstreams, validate registry collisions, reject stale bases and protected/foreign path changes, and apply status transitions.
- `change_impact.py` — map changed files to affected approved tasks and required regression.
- `regression_runner.py` — execute the union of universal and impact-selected mandatory suites, or emit a plan with `--plan-only`.
- `evidence_capture.py` — deterministic still-evidence capture orchestration and metadata.
- `motion_capture.py` — full-cycle/slow/turn/transition/contact/clipping evidence orchestration for character and animal motion tasks.
- `save_state_matrix.py` — fresh/current/previous/interrupted/reload/migration/recovery persistence matrix.
- `device_matrix.py` — early phone/tablet/foldable layout and lifecycle matrix.
- `evidence_packager.py` — package exact source hashes, changed files, tests, logs, screenshots/videos, performance records, raw critic material, failures and dispositions.
- `critic_harness.py` — prepare/validate applicable specialist-critic records; never converts builder self-review into an independent pass.
- `closure_validator.py` — final task-candidate closure gate; mandatory reviewed dimensions must be strictly `>9.0` unrounded.
- `validate_migration.py` — verify the V2 governance migration itself, including T01/T02 preservation, T03 recovered state, all 70 tasks, all 11 critics, budgets and allowed migration paths.

Authoritative coordination data lives in `Docs/Production/`:
`DEPENDENCY_GRAPH.json`, `WORKSTREAM_REGISTRY.json`, `PATH_OWNERSHIP.json`, `CRITIC_MATRIX.json`, `PERFORMANCE_BUDGETS.json`, `REGRESSION_MATRIX.json`, `SAVE_STATE_MATRIX.json`, `DEVICE_LAYOUT_MATRIX.json`, task packets, change requests and evidence manifests.

No tool here may mark an isolated builder branch production-APPROVED. Only the integration owner can approve after integration, impact regression, fresh evidence, applicable critics and G1–G14 closure. T68/T69 remain the only final physical native-4K/60 certification tasks.
