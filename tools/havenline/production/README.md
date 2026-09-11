# Havenline Production Accelerator

`production_cli.py` is the stdlib-only governance/acceleration entry point.

Commands:
- `validate-registry` — validates active dependency/path ownership collisions.
- `validate-candidate TASK FILE...` — rejects protected, foreign-owned, shared-integration or out-of-scope paths; `--integration-owner` permits integration-owner coordination paths but not foreign protected runtime.
- `impact FILE...` — maps changed files to impacted approved/active tasks.
- `regression-plan FILE...` — universal baseline + mandatory impacted regression suites.
- `task-packet TASK --output FILE` — freezes assignment values against current integration commit.
- `capture-plan TASK [--motion]` — deterministic still/motion evidence contract.
- `save-matrix TASK` — fresh/existing/previous/interrupted/reload/migration/recovery matrix.
- `device-matrix TASK` — phone/tablet/foldable early layout matrix.
- `package TASK --candidate SHA --changed ... --output ZIP` — source-bound evidence package manifest + digest.
- `closure MANIFEST` — candidate closure validator; mandatory critic dimensions must be strictly `>9.0` unrounded.

The CLI never awards an independent critic pass, never certifies physical 4K/60, and never marks a task APPROVED. Approval is an integration-owner registry/task-gate mutation after G1–G14 are satisfied.

Large binary evidence remains in Actions artifacts or equivalent hashed storage; `Docs/Production/Evidence/` stores manifests, artifact IDs/digests, raw-review references and dispositions.
