# T13 Task Packet — Progressive Difficulty & spend-blind Challenge Director

- Future branch: `havenline/T13-challenge-director`
- Future owner: `challenge-director-builder`
- Planned alias: `@reservation:T13`
- Dependencies: T12
- Required critics: C2, C3, C4, C6, C7
- Runtime build before activation: **FORBIDDEN**

## Planned owned paths
- `HavenlineGodot/scripts/challenge_director.gd`
- `HavenlineGodot/data/challenge_director_v1.json`
- `HavenlineGodot/tests/test_task13_challenge_director.gd`
- `HavenlineGodot/tests/test_task13_integration.gd`
- `HavenlineGodot/tests/capture_task13_challenge.gd`
- `Docs/Production/T13/**`
- `tools/havenline/task13/**`
- `.github/workflows/havenline-task13-*.yml`

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
Only after every dependency is APPROVED/integrated and ownership is released:

1. re-read exact current integration head;
2. rebind T12 consumer contract and Game Master policy/standard;
3. recheck planned path ownership and refresh contract hashes;
4. run `python3 tools/havenline/t13_t20/prepare_activation.py --task T13 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>`;
5. apply the emitted reservation/claim through the integration owner;
6. create/rebase `havenline/T13-challenge-director` from the exact post-activation head;
7. require candidate guard PASS before runtime/data expands.

Preparation artifacts do not grant activation by themselves.
