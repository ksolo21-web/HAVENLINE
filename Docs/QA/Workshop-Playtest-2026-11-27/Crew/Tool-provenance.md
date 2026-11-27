# Survivor tools

The approved gameplay assets are the same shapes used by the player's current tool controller. The survivor uses a fitted two-handed pose suited to each working tool. Texture and geometry selection follow the current trial branch.

| Tool | Gameplay asset | SHA-256 |
|---|---|---|
| Axe | `HavenlineLevel1/assets/tools/axe-field-grip.glb` | `f168b18ad31bc500d39808e63a9fadf14a2e85b23090e6dea60ef64c3646cecc` |
| Pickaxe | `HavenlineLevel1/assets/tools/pickaxe-meshy.glb` | `bd7ee0799346d61c22d6ff54ba7c5a03305616c0c32ac19c7d3c1534b6f1c623` |

The previous worker loaded an alternate `companion_axe.gltf` from the settlement-person assets. The game controller already uses the fitted approved axe. The pickaxe geometry was already present in the worker scene. Each tool needs its own handle grip, strike direction, and scale check.

[Selected gameplay controller](https://github.com/ksolo21-web/HAVENLINE/blob/b92588e389f429776a11e7d0349d2096311000ca/HavenlineLevel1/weapon_orbit.gd) · [Axe fit revision](https://github.com/ksolo21-web/HAVENLINE/commit/949af6f09)
