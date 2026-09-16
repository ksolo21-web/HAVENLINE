# T10 handoff tooling review

Scope: tooling/governance only. This review does not alter T10 runtime semantics, approve T10, bind the real T09 adapter, or permit integration before dependency closure.

## Defects repaired

1. `prepare_reconciliation.py` duplicated an incomplete hard-coded list of T10-owned workflow files. It could reject legitimate future T10 workflow additions even when `ACTIVATION_CHECKLIST.json` reserved `.github/workflows/havenline-task10-*.yml`.
   - Repair: candidate ownership is now read from the exact isolated candidate's `Docs/Production/T10/ACTIVATION_CHECKLIST.json` and matched directly against `planned_owned_paths`.
   - Fail-closed checks: missing/wrong/duplicate reservation data fails; foreign task workflows and integration-only runtime remain outside T10 ownership.

2. `havenline-task10-world-transformation.yml` assumed a live T10 `WORKSTREAM_REGISTRY` row on every T10 branch push. That is impossible during the explicitly supported `BUILT_PENDING_DEPENDENCY` phase before T09 approval/activation, producing `StopIteration` before source/runtime tests ran.
   - Repair: the workflow now distinguishes registered integration candidates from checklist-authorized preactivation candidates.
   - Registered mode retains `workstream.py validate-candidate` against the recorded exact base.
   - Preactivation mode requires the isolated governance preflight plus clean exact-base reconciliation, no unauthorized paths, `integration_allowed=false`, `task_approved=false`, and unresolved dependency closure. If dependencies are fully approved, preactivation fails and formal T10 activation/registration is required.

## Review tests

`tools/havenline/task10/tests/test_prepare_reconciliation.py` verifies the full current T10 workflow family is covered by the authoritative reservation while T11 workflow and `simulation.gd` remain excluded.

The adapter-preflight workflow now runs on pull requests into `havenline/T10-world-transformation` and executes these tooling regression tests before validating the post-T09 adapter contract/reconciliation shape.
