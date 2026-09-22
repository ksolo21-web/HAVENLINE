# T13 Task Packet — Progressive Difficulty & spend-blind Challenge Director

- Future branch: `havenline/T13-challenge-director`
- Future owner: `challenge-director-builder`
- Planned alias: `@reservation:T13`
- Dependencies: T12
- Required critics: C2, C3, C4, C6, C7
- Runtime build before activation: **ISOLATED BUILD ALLOWED** — maximum state `BUILT_PENDING_DEPENDENCY`; integration/approval remain forbidden.

## Planned owned paths
- `HavenlineGodot/scripts/challenge_director.gd`
- `HavenlineGodot/data/challenge_director_v1.json`
- `HavenlineGodot/tests/test_task13_challenge_director.gd`
- `HavenlineGodot/tests/test_task13_integration.gd`
- `HavenlineGodot/tests/capture_task13_challenge.gd`
- `Docs/Production/T13/**`

## Prepared builder handoff
Read these before implementing any T13 runtime code:

1. `Docs/Production/T13/FROZEN_SCOPE.md` — authoritative scope/exclusions.
2. `Docs/Production/T13/PREBUILD_CONTRACT.json` — dependency-independent preparation contract.
3. `Docs/Production/T13/T12_CONSUMER_BINDING.json` — exact T12 consumer boundary; must be rebound at activation.
4. `Docs/Production/T13/IMPLEMENTATION_BLUEPRINT.md` — spend-blind architecture, deterministic decision model, bounds/recovery, GM isolation, activation-time rebind.
5. `Docs/Production/T13/TEST_EVIDENCE_PLAN.md` — replay, spend-blind equivalence, anti-spike, malformed-policy, T12 integration, GM isolation, evidence/critic matrix.
6. `Docs/Production/T13/ACTIVATION_CHECKLIST.json` — fail-closed activation sequence.
7. `Docs/Production/T13/defect-ledger.json` — preparation defect/blocker state.

## Mandatory forward contracts
These are external bindings, not files T13 may recreate while dependency-locked:

- `Docs/Production/GAME_MASTER_ACCOUNT_STANDARD.md`
- `Docs/Production/GAME_MASTER_POLICY.json`
- `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
- `Docs/Production/DEPENDENCY_GRAPH.json`
- `Docs/Production/CRITIC_MATRIX.json`

If an external contract is absent or changed at activation, stop and reconcile it through the approved interface/change process. Do not manufacture a substitute inside T13.

## Required proof
- spend-blind input-flow audit and paired equivalence fixtures;
- deterministic difficulty replay;
- bounded escalation, recovery, hysteresis and anti-spike proof;
- malformed-policy deterministic safe fallback;
- T12 consumer-contract integration proof;
- GM profile authorization/isolation and elevated-envelope proof;
- exact-source C2/C3/C4/C6/C7 evidence;
- all mandatory dimensions strictly >9.0 unrounded, target 10/10;
- zero unresolved mandatory defects.

## Activation start rule
The isolated builder may be constructed before T12 approval under `preactivation_candidate.py`, but it may not activate or integrate. After every dependency is APPROVED/integrated and ownership is released:

1. re-read exact current integration head;
2. rebind T12 consumer contract and Game Master policy/standard;
3. recheck the six planned T13 paths against current active/integration-only ownership and refresh contract hashes;
4. require repository-wide production governance/migration validation PASS for the exact preparation candidate;
5. through the integration owner, add `@reservation:T13` using the exact six planned paths from `ACTIVATION_CHECKLIST.json`;
6. claim T13 as ASSIGNED with the checklist's canonical `workstream.py claim` command on the exact post-reservation integration head;
7. require `python3 tools/havenline/production/task_graduation_gate.py T13 --target ASSIGNED --integration-head <EXACT_POST_CLAIM_INTEGRATION_HEAD>` to PASS;
8. create/rebase `havenline/T13-challenge-director` from that exact post-assignment head;
9. require the existing isolated candidate guard and BUILDING_ISOLATED graduation package to PASS before T13 runtime/data expands.

Preparation artifacts do not grant activation by themselves.

## Existing canonical activation controls
T13 does not self-author governance tooling. Activation and branch graduation reuse the already-integrated production controls under `tools/havenline/production/`, especially `workstream.py`, `task_graduation_gate.py`, `preactivation_feasibility.py`, and the repository-wide governance/candidate workflows.

## Preactivation isolated build lane

While T12 is unresolved, `havenline/T13-challenge-director` may implement only the six frozen T13-owned paths. The canonical `tools/havenline/production/preactivation_candidate.py` must PASS against the exact candidate. The maximum legal state is `BUILT_PENDING_DEPENDENCY`; `ASSIGNED`, `INTEGRATION_READY`, integration, and task approval remain forbidden. Any T12 consumer-contract or Game Master contract drift invalidates affected preactivation evidence and requires reconciliation/retest.
