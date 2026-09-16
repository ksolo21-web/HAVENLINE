# T13 Task Packet — Progressive Difficulty & spend-blind Challenge Director

- Future branch: `havenline/T13-challenge-director`
- Future owner: `challenge-director-builder`
- Planned alias: `@reservation:T13`
- Dependencies: T12
- Required critics: C2, C3, C4, C6, C7

## Planned owned paths
- `HavenlineGodot/scripts/challenge_director.gd`
- `HavenlineGodot/data/challenge_director_v1.json`
- `HavenlineGodot/tests/test_task13_challenge_director.gd`
- `HavenlineGodot/tests/test_task13_integration.gd`
- `HavenlineGodot/tests/capture_task13_challenge.gd`
- `Docs/Production/T13/**`
- `tools/havenline/task13/**`
- `.github/workflows/havenline-task13-*.yml`

## Mandatory forward contracts
- `Docs/Production/GAME_MASTER_ACCOUNT_STANDARD.md`
- `Docs/Production/GAME_MASTER_POLICY.json`
- `Docs/Production/HAVENLINE_BUILD_PLAN_V2.md`
- `Docs/Production/DEPENDENCY_GRAPH.json`
- `Docs/Production/CRITIC_MATRIX.json`

## Required proof
- spend-blind input audit
- deterministic difficulty replay
- bounded escalation/recovery proof
- GM role-isolation proof
- exact-source critic evidence

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T13 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, apply the emitted reservation/claim through the integration owner, then create/rebase the future branch from the exact post-activation head.
