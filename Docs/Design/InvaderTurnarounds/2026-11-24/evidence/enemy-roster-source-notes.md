# Havenline invader render roster — source evidence

Research date: 2026-11-24. Scope: read-only source/roster planning for isolated concept-reference PNGs. This document does not activate T21, change gameplay, approve models, or certify animation.

## Roster frozen for this render batch

The bounded recovered roster contains **three archetypes**. Only the hostile wolf is implemented in the inspected Godot simulation. Raider and Ice Brute are earlier conversation/prototype concepts recovered by the coordinating agent; they are not current source-defined enemy catalog entries.

| Render key | Name | Authority and status | Exact runtime ID / defined equipment |
|---|---|---|---|
| `hostile_wolf` | Hostile wolf | Current simulation and original gameplay contract. Actual approved hostile art is still absent from this inspected source. | Tuning key `wolf`; spawned instance ID is `"wolf" + str(threat_serial)`, e.g. `wolf1`. No wearable equipment or hostile color specification is defined. The render key is new artifact organization, not a renamed runtime ID. |
| `raider` | Raider | Planned human hostile recovered from prior conversation. The coordinator reports a September user confirmation of hostile wolves/raiders. No current raider enum, catalog entry, prefab, model, weapon allocation, faction insignia or tier definition was found in the inspected source. | No verified source ID. Any winter outfit, weapon, armor, scars or colors in this batch are concept design decisions, not recovered canon. |
| `ice_brute` | Ice Brute | Larger/stronger prototype boss recovered from earlier assistant native-alpha output by the coordinator. No current source-defined boss entry or user-approved appearance was recovered in this scan. | No verified source ID, proportions, equipment, material, or named tier. Keep prototype/concept status explicit. |

There is **no substantiated tier/elite/faction variant roster** in the inspected sources. Later wolf waves increase quantity (`2 + wave`) while using the same `wolf` tuning. Do not reinterpret these as separate enemy variants.

## Exact source bindings

Repository: `ksolo21-web/HAVENLINE`.

| Source role | Branch/ref | Exact inspected head |
|---|---|---|
| Current native Godot source | `codex/havenline-godot-android` | `4cc278f13462ad1678c3dbed9153e8badce59686` |
| Forward task preparation | `havenline/governance-all-t13-t70-ready` | `426d7973fb64af0ef33208bdb50fd859de58fb0a` |
| Legacy Unity character review check | `agent/havenline-v7-unity-review` | `dd36c73ce9042b85581bf5667ae8323c2f4e5a3b` |
| Existing art-reference archive, separate from hostile runtime | `art/resource-turnarounds-2026-11-23` | `25b4ec6dd407c1c2530a3781527df64eabb63b99` |

### Runtime evidence

1. [`HavenlineGodot/scripts/simulation.gd`](https://github.com/ksolo21-web/HAVENLINE/blob/4cc278f13462ad1678c3dbed9153e8badce59686/HavenlineGodot/scripts/simulation.gd), blob `8b21954cc6771e99545a23b984b1890ad6e4c28f`. `step_threats` at lines 316–358 is the inspected spawn/behavior implementation. Line 325 emits only wolf instances. Wolves approach the furnace, intercept a built barricade, or target a nearby player. They move, attack on a cooldown, and stop participating after health reaches zero. No other hostile archetype or boss switch is present there.
2. [`HavenlineGodot/data/reference-contract.json`](https://github.com/ksolo21-web/HAVENLINE/blob/4cc278f13462ad1678c3dbed9153e8badce59686/HavenlineGodot/data/reference-contract.json), blob `5c4ce6470006c5b18735e0835571b817e54e2fdc`. Lines 140–153 define a 48-second first-wave delay, three enemies in wave one, and one `wolf` tuning block: health 65, move speed 3.9, attack interval 1.1 seconds. These are behavior parameters, not visual scale or art specifications.
3. [`HavenlineGodot/scripts/main.gd`](https://github.com/ksolo21-web/HAVENLINE/blob/4cc278f13462ad1678c3dbed9153e8badce59686/HavenlineGodot/scripts/main.gd), blob `046d8f133f4aed0304d1785299f4cb046747ebca`. Lines 64–67 explain the fail-closed presentation safeguard and set `sim.threats_enabled = false` so unapproved/invisible wolves cannot damage the player. Therefore a generated concept sheet must not be described as an integrated or approved runtime hostile.
4. [`Docs/AI/HavenlineProjectContext.md`](https://github.com/ksolo21-web/HAVENLINE/blob/4cc278f13462ad1678c3dbed9153e8badce59686/Docs/AI/HavenlineProjectContext.md), blob `05819c521709bfc868c35ff0297fffd1d482ac01`. Preserves the first three-wolf wave, proximity combat, close orthographic camera, and simple movement-led controls.
5. [`HavenlineGodot/data/npc-catalog.json`](https://github.com/ksolo21-web/HAVENLINE/blob/4cc278f13462ad1678c3dbed9153e8badce59686/HavenlineGodot/data/npc-catalog.json), blob `4222c9ba09c13f99b2862f7553e5412106999e0f`. `pet_wolf_01` is a friendly companion entry, not another hostile. The seven animal companion species do not establish seven enemy species.

### T21 scope evidence

At `426d7973fb64af0ef33208bdb50fd859de58fb0a`:

- [`Docs/Production/T21/TASK_PACKET.md`](https://github.com/ksolo21-web/HAVENLINE/blob/426d7973fb64af0ef33208bdb50fd859de58fb0a/Docs/Production/T21/TASK_PACKET.md), blob `9ad2de01095d880c1ee603eefb085c94f5c6d4dd`.
- [`Docs/Production/T21/FROZEN_SCOPE.md`](https://github.com/ksolo21-web/HAVENLINE/blob/426d7973fb64af0ef33208bdb50fd859de58fb0a/Docs/Production/T21/FROZEN_SCOPE.md), blob `806a0ea8702396a9cc6f57e92db8415024a7d475`.
- [`Docs/Production/T21/PREBUILD_CONTRACT.json`](https://github.com/ksolo21-web/HAVENLINE/blob/426d7973fb64af0ef33208bdb50fd859de58fb0a/Docs/Production/T21/PREBUILD_CONTRACT.json), blob `9ed8a7a6ca16c20879cc6a9c4b50c8a67ec69a43`.

T21 requires visible hostiles, hunting, contextual weapon selection/progression, attack/contact timing, readable impacts, hostile reactions/defeat and loot conservation. It does **not** enumerate species, raider classes, boss tiers, weapon models, enemy outfit designs, or an all-biome enemy roster. Its planned paths are forward scope, not proof those assets exist. The inspected task packet remains preparation for future runtime work.

### Bounded legacy check

The current branch retains only editor/review Unity C# scripts, tutorial scripts and `Assets/Scenes/SampleScene.unity` alongside the Godot scene. The scene blob is `1c63aa8ded8c325623e162675b13bfcd0b50aa5a`. Read-only code/scene and named-enemy searches found no additional distinct hostile in the current branch or the inspected `agent/havenline-v7-unity-review` branch. This is a bounded source check, not a claim to have audited every historic commit or removed repository.

The supplemental Whiteout ad notes mention polar-bear/enemy-wave escalation as **external visual/gameplay reference**. This does not establish a Havenline polar-bear hostile or an approved boss roster.

## Render evidence coverage

The coordinating agent selected two concept-reference sheets per archetype:

1. Eight evenly spaced, consistent-scale turnaround views spanning a full 360 degrees. Check front/rear identity, left/right anatomy, silhouette, outfit/gear attachment continuity, proportions, paws/hands, and unobscured feet.
2. Closeups and use-state board: face/head, body material/garment detail, equipment/grip where present, ready/approach stance, clear attack pose, hit reaction and non-graphic defeated/rest state. Use the wolf's native anatomy; use readable hand/weapon contact for proposed humanoid equipment.

These views are concept-review evidence. A collection of generated poses is not a verified animation cycle, a rig, a 3D mesh, or a gameplay implementation. Human and boss gear and visual details that are absent from source should remain marked as proposed art decisions.

## Acceptance boundary

The render batch is complete only when all three source-bounded archetypes have both required sheets, all selected sheets pass the independent visual review, and the deliverable PNGs plus provenance/evidence are committed directly to the requested GitHub branch. Missing hostile catalogs for later biomes cannot be filled by inventing additional canon. No runtime source was modified by this source-planning work.
