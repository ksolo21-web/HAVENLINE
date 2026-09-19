# Havenline V2 Governance Migration — Resumable Checkpoint

## Status
The controlled parallel-production governance migration is complete and validated. This checkpoint does **not** approve T03 and does not start T04+ runtime work.

## Recovered baseline and preserved history
- Integration branch: `codex/havenline-sequential-task-01`.
- Recovery head before migration: `f26b3d6d5a788c03192f593936bfe8ce5ccfc5bc`.
- Pre-V2 plan source commit: `6947849f581db9cfa53a17ff9202ecde1c0ee80c`.
- Pre-V2 plan archived byte-for-byte at `Docs/Production/Archive/SEQUENTIAL_REPAIR_PLAN.pre-v2.2026-09-11.md`.
- T01 remains APPROVED at accepted source `45ba7905cd468c229cd61364f4d1ac45b14d3e5e`.
- T02 remains APPROVED at accepted source `1f0ba3bede3d160a34751c2fcdbfa78c1b6785ff` with authoritative `river_v1_mapspan` geometry.
- No runtime game file under `HavenlineGodot/` was modified by the governance migration itself.

## Authoritative V2 coordination
- `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
- `Docs/Production/SEQUENTIAL_REPAIR_PLAN.md`
- `Docs/Production/task-gates.json`
- `Docs/Production/DEPENDENCY_GRAPH.json`
- `Docs/Production/WORKSTREAM_REGISTRY.json`
- `Docs/Production/PATH_OWNERSHIP.json`
- `Docs/Production/CRITIC_MATRIX.json`
- `Docs/Production/PERFORMANCE_BUDGETS.json`
- `Docs/Production/REGRESSION_SUITES.json`
- `Docs/Production/TASK_PACKET_TEMPLATE.md`
- `Docs/Production/ChangeRequests/`
- `Docs/Production/Evidence/`
- `tools/havenline/production/production_cli.py`
- `tools/havenline/production/critic_harness.py`
- `tools/havenline/production/test_production_cli.py`
- `.github/workflows/havenline-production-governance.yml`

## Validation performed
GitHub Actions governance validation run `34648061663`, job `103423489800`: PASS.

Verified in that run:
- migration did not alter `HavenlineGodot/` runtime files relative to the recovered migration baseline;
- archived pre-V2 plan matched the exact recovered source bytes;
- coordination JSON parsed successfully;
- active workstream registry/path ownership validation passed;
- production accelerator migration test suite passed **12/12**;
- the closure validator accepts `9.01` but rejects exactly `9.0`, implementing the forward strict `>9.0` rule.

A final governance validation must also pass after this checkpoint/registry sealing commit. Its run ID should be appended to this file or a successor checkpoint when available.

## Exact T03 resume point
T03 — Fences, gates and navigable work lanes — **FIX_REQUIRED**.

Candidate/evidence source: `6947849f581db9cfa53a17ff9202ecde1c0ee80c`.

Current verified construction evidence:
- 16 functional/regression suites;
- 807 checks PASS;
- 9 T01 geometry checks PASS;
- 61 source-bound renders verified;
- 11 native 3840×2160 scale-1 renders;
- no T01/T02 authority discarded.

Current critic evidence:
- C1 Reference Fidelity and C2 Technical/Visual Integrity were actually executed;
- 22/22 judgments are present;
- combined gate artifact `10279571441`, SHA256 `ae830b988f88dd8a8d680272fd3eb00c2a900c6ae51949703f86bfe372ceec78`;
- failing evidence group: `river-gates`;
- C2/visual-integrity minimum: **2.0/10**;
- C1/reference-fidelity minimum: **4.0/10**;
- unresolved mandatory river-gate defects remain;
- C6 Performance Critic is now required by the V2 critic matrix but has **not yet been independently executed** for T03.

Therefore T03 cannot pass G12/G13 and cannot be APPROVED. Do not manufacture or infer a critic pass.

## Next executable action
Resume T03 from the exact candidate/evidence checkpoint. Repair only the grounded river-gate readability/finish defects within T03's already-frozen scope. Do not alter the approved T02 river authority or implement bridges/T04+ behavior. Then:
1. run path/scope/dependency validation;
2. run impact-selected mandatory regression plus T03 tests;
3. recapture fresh source-bound evidence if runtime/pixels changed;
4. execute independent C1 + C2 + C6 at $0 cost where available;
5. require every applicable mandatory dimension **strictly >9.0 unrounded** and no mandatory defect;
6. run G14 on the integrated candidate;
7. only then mark T03 APPROVED and unlock Wave 1.

## First safe post-T03 parallel assignments
Remain LOCKED until T03 is approved:
- Workstream A — T04 — `havenline/T04-camera`.
- Workstream B — T05 — `havenline/T05-props`.
- Workstream C — T06 — `havenline/T06-character1`.
- Workstream Q — QA/integration infrastructure only — `havenline/QA-integration` — may be PREPARED because it has no unrelated runtime scope.

No builder may modify a foreign-owned/protected path. Cross-workstream needs go to `Docs/Production/ChangeRequests/` for integration-owner resolution.
