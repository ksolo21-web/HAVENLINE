# PR #108 rock strike eligibility, detached proposal

Exact candidate commit `48c6c53a0dfda117ef12c68b32cfe2b3732d5239`, base opening blob `6a0f08cffba3d8cacea506e9150e44298e3bc394`. The independently walked pre-repair route paid the camp, stood on the inside of the west wall and struck the outside rock with F while a layer-1 collision ray hit that wall. Hardware input was not used; controls were passed through the integrated scene's normal input handler.

The patch shares one check between the existing rock target decision and actual request. It first preserves the old seated/distance/facing conditions, then requires a clear horizontal ray 0.35m above actor ground toward the rock's planar center. It checks solid physics bodies in the existing camp collision layer (1) and excludes the actor body, with hit-from-inside enabled. If the world is unavailable it denies mining. The PR's rock is a mesh-only node, so the ray does not strike it. The original F fallback path for trees is unchanged. No changes to tree behavior, input mapping, picking or rewards, animation, materials, geometry, or production. This narrow single-ray check is neither a swept pickaxe collision test nor proof of reach across slopes, under railings, at all actor heights, or on an Android device.

The one-file patch passed `git apply --check`, a disposable application gives blob `1475395f76045d41931dd3e0dd2d5a7e28fc4f36` (see exact SHA in checks below), and reverse validation succeeded. No real profile or original checkout is touched.

## Serial native replay

Requires pinned sparse checkout and an individually granted existing headless lease. Run separately:
```sh
bash run.sh <checkout> <lease-file> baseline
bash run.sh <checkout> <lease-file> repaired
```
Both runs use a fresh archive, exact tracked GLBs, a fresh disposable HOME/XDG profile, exact integrated opening and no persistence. The controls route walks three-wood opening, pays once, confirms a real collider at the west wall, injects F, then walks out via South gate to the rock. The baseline witness expects 1 rock strike from inside to preserve the negative control and 2 accepted outdoor hits. Patched expects 0 inside and 3 outdoor, with unchanged mining sequence on the blocked press and no ledger side effects. Both check wall presence, legal distance/facing, an actually clear legal ray, exhausted rock on 3 accepted blows, and unchanged ledger from payment on. Any failed upstream waypoint marks downstream unobserved, not passed. Missing touch action, stock reward, confirmed pickaxe-frame contact, and visual/device acceptance remain out of scope.
