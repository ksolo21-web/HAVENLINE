# Havenline · World One

Play the normal opening scene `res://field_opening.tscn` from `e978a44b1b112bb598f9ec1724b3616ec80e6970` on `trial/world-one-expansion-2026-11-26`. The three downloads are a Linux build, an Android arm64 debug APK and the Godot 4.7.2 source project. The trial uses its own save identity. [Builds and instructions](Build/README.md) · [Source manifest](Build/Reviewed-files.json)

## Footage for Alfred

- [World One opening and camp progression](Gameplay/World-One-Gameplay.mp4) · [Chapter guide, source commits and native 4K views](Gameplay/Gameplay-QA.md)
- [Wolf attacks, player HP, defeat and both return locations](Gameplay/Combat-and-Recovery.mp4)
- [Tree impacts, felling and five-second regrowth](Gameplay/Resource-Regrowth.mp4)
- [Storehouse upgrades, loading doors and occupied bays](Storage/House/Three-storage-tiers.jpg) · [Storage organization](Storage/House/Storage-access-and-organization.jpg)
- [Reference camp and gameplay scale](Landmark-scale/README.md) · [Fence and gate comparison](Perimeter/Reference-and-runtime.jpg)

The 28.4-second main film contains 23 chapters. Its main sequence follows one 293.5-second playthrough. Two labeled appendices show harvest regrowth from a separate run on the same commit. The player bought all eight upgrades, spent 18 wood, 8 stone and 2 meat, traveled 100.79 m from camp and returned. Both gates were crossed each way at each camp size. All three material balances reconciled across 17,612 physics ticks. [Earned route](Gameplay/Evidence/Gameplay-route.json)

## What changed

| Area | Behavior in this build |
| --- | --- |
| Furnace and quarry | The recovered furnace and its collider are 24% smaller in each dimension. Its visible width fell from 1.95 to 1.48 standing-player heights at the gameplay camera. Active stone banks are 70% larger and measure 1.03 player heights across. The exported rock, collider, remote instance and pick contact agree. [Measurements](Landmark-scale/Measurements.json) |
| Harvest | The blade contact drives a pine’s impact direction, splinters and snow. Three strikes fell it and release three wood. Wood returns after five seconds of active simulation, including its growth animation. Stone returns in 32 seconds. [Tree timing and native frames](Lifecycle/Trees/README.md) |
| Plots and equipment | The three-wood first purchase builds the furnace, both gates and fence. The first expansion offers one storehouse in the northwest. Each tier is a separate paid visit. The last expansion offers the eastern watchtower and the extra orbiting axes. [Prices, controls and saves](https://github.com/ksolo21-web/HAVENLINE/blob/e978a44b1b112bb598f9ec1724b3616ec80e6970/HavenlineLevel1/docs/Field-Loop.md) |
| Storage | Rope bindings identify the starter, iron bands and masonry identify the reinforced tier, and blue riveted siding identifies the advanced tier. Approach opens both sliding doors, then the threshold reveals its slate aisle and typed bins. Each individual unit can fly from a bin to pay a cost. [Storage review](Storage/README.md) |
| Backpack | Wood, stone and meat keep separate positions and the HUD counts every unit. The displayed load now fits the actual camera at a gate or in front of the storehouse, including at pinch zoom. Every further pickup, deposit and payment still travels to or from the top visible item. [Before and after at the east gate and storehouse](Carry/Source-and-high-load-comparison.jpg) · [Measurements](Carry/README.md) |
| Enemy attacks and player health | Wolves pursue, brace and bite. Normal bites cost one HP and an alpha bite costs two. The hero has four HP. The HUD, body recoil and damage numbers react immediately. Zero HP plays the fall and disables the orbit. The player returns at full health and receives two seconds of protection. Before the hearth purchase the return point is the first buy plot. After purchase it is inside the camp. [Combat footage](Gameplay/Combat-and-Recovery.mp4) |
| World One | The 1,024 m square snowfield contains 34,480 outer harvest sites and the opening grove. Bootprints and wolf tracks fade in 17 seconds. New encounters roll every 24 seconds when space is available, with up to four living wolves and an 18% chance of an alpha per successful encounter. The eastern tower fires independently, and the hero's equipped orbit resumes immediately outside the purchased perimeter. [World map and survey](World/README.md) |

The combat and regrowth films were recorded on the immediately preceding 34df87a8 build. The subsequent gameplay change was confined to backpack presentation and its transfer endpoints. Combat and harvest were re-tested on the corrected build. The main progression film and the high-load review identify their own source.

The field, camp and threat scores crossfade with play. Footsteps, tool impacts, resource transfers, purchases, tree returns, door movements, bites, damage, falls and rescues have event-triggered sound. [Audio implementation](https://github.com/ksolo21-web/HAVENLINE/blob/e978a44b1b112bb598f9ec1724b3616ec80e6970/HavenlineLevel1/field_audio.gd)

The review covers this Level 1 opening and its world systems. The project’s wider T01–T11 sign-off and sustained 4K60/120 on physical phones and tablets are still open. [Independent visual review](Independent-review.md) · [Task-plan status](Task-plan-review.md)
