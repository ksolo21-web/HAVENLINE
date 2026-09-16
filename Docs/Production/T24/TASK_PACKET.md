# T24 Task Packet — Guardian dog

- Future branch: `havenline/T24-guardian-dog`
- Future owner: `guardian-dog-builder`
- Planned alias: `@reservation:T24`
- Dependencies: T06, T07, T14
- Required critics: C1, C2, C5, C6

## Planned owned paths
- `HavenlineGodot/scripts/companion_guardian_dog.gd`
- `HavenlineGodot/data/companion_guardian_dog_v1.json`
- `HavenlineGodot/assets/companions/t24_guardian_dog/**`
- `HavenlineGodot/animations/companions/t24_guardian_dog/**`
- `HavenlineGodot/tests/test_task24_guardian_dog.gd`
- `HavenlineGodot/tests/capture_task24_guardian_dog.gd`
- `Docs/Production/T24/**`
- `tools/havenline/task24/**`
- `.github/workflows/havenline-task24-*.yml`

## Required proof
species-specific locomotion; retrieve/work behavior; lunge/bite/intercept attack; ground/contact/clipping/gear review; save/restore; gameplay-scale + front/rear/left/right/3/4/overhead/close motion views.

## Start rule
Run `python3 tools/havenline/t21_t32/prepare_activation.py --task T24 --activate --base <EXACT_CURRENT_INTEGRATION_HEAD>` after T14 clears.
