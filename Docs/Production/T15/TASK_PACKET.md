# T15 Task Packet — Customer/NPC models, crowds and routing

- Future branch: `havenline/T15-npc-routing`
- Future owner: `npc-routing-builder`
- Planned alias: `@reservation:T15`
- Dependencies: T04, T05, T06, T07, T14
- Required critics: C2, C3, C4, C6, C1

## Planned owned paths
- `HavenlineGodot/scripts/customer_npc_director.gd`
- `HavenlineGodot/scripts/npc_routing.gd`
- `HavenlineGodot/data/customer_npc_profiles_v1.json`
- `HavenlineGodot/assets/npcs/t15_customers/**`
- `HavenlineGodot/tests/test_task15_npc_routing.gd`
- `HavenlineGodot/tests/capture_task15_npcs.gd`
- `Docs/Production/T15/**`
- `tools/havenline/task15/**`
- `.github/workflows/havenline-task15-*.yml`

## Required proof
route/queue determinism; collision/lane clearance; crowd density/performance; multi-angle visuals; save/restore of NPC-safe state where applicable.

## Start rule
Run `python3 tools/havenline/t13_t20/prepare_activation.py --task T15 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after dependencies clear, then apply the emitted reservation/claim and create/rebase the future branch.
