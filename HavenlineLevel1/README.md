# Havenline Level 1 settlement trial

On this trial branch, `res://field_opening.tscn` opens World One. The player can build the camp, purchase the survivor plot, hunt with the owl, work the shore machines and serve customers through the north fence. The recorded playthrough starts with an empty test profile. [Gameplay, controls, downloads and audit](../Docs/QA/Level-1-Settlement-2026-11-26/README.md) · [Rebuild exactly this game](../Docs/QA/Level-1-Settlement-2026-11-26/Source/README.md)

## Earlier opening experiments

The instructions below describe the historical opening and its own entry point.

This separate preview is for the revised **opening**, not the full Level 1 game or a release. The canonical `HavenlineGodot/` project, its task plans and original assets stay intact. The development base is `codex/havenline-sequential-task-01` at `f74a84a2a288ab3d3935fba7a6cb9b975c2df239`.

## Run the archived combined opening

Use a fresh disposable checkout of the replacement branch. Importing the project and pressing F5 runs the deliberately unchanged V8 baseline (`res://opening.tscn`), **not** this preview. To test the combined river, camp, HUD, and Character 1 animation, use the exact scene below.

From the repository root with Python 3.11+ and Godot 4.7.2 (Linux shell; use an isolated runner with a desktop display for the final command):

```sh
python3 HavenlineLevel1/tools/hydrate_assets.py
profile="$(mktemp -d)"
mkdir -m 700 "$profile/home" "$profile/data" "$profile/cache" "$profile/config" "$profile/runtime" "$profile/tmp"
export HOME="$profile/home" XDG_DATA_HOME="$profile/data" XDG_CACHE_HOME="$profile/cache"
export XDG_CONFIG_HOME="$profile/config" XDG_RUNTIME_DIR="$profile/runtime" TMPDIR="$profile/tmp"
godot --headless --path HavenlineLevel1 --editor --import --quit
godot --path HavenlineLevel1 --scene res://previews/integrated_opening.tscn
```

Hydration verifies all four studio files and restores the exact furnace from the tracked pieces. Do not pass save or fixture flags to the rendered run. Controls: WASD or arrows to move, **F** to chop, **E** to operate the nearest gate. The ordinary combined preview does not write opening saves.

## Evidence and limits

- [Combined opening](docs/COMBINED_OPENING_VERIFICATION.md): independent scripted movement, raised resource pickup, paid camp and both gates; desktop smoke also confirmed the narrow HUD and animations below.
- [Disposable cold restart](docs/COMBINED_COLD_VERIFICATION.md): scoped paid/unpaid receipts and failed staging write. These are explicit test fixtures, not shipped save behavior.
- [Compact HUD](docs/COMPACT_HUD_VERIFICATION.md) and [Character 1 playback](docs/HERO_LOCOMOTION_VERIFICATION.md): desktop prompt clearance and no static idle T-pose. Full gait, foot contact and two-handed axe performance are not approved.
- [Provisional dry-bank route](docs/MANUAL_SHORE_ROUTE_VERIFICATION.md): tested East-gate out and back, no casting, fishing grant or placement approval.

Keep the approved river and forest, one revised camp, both gates, and exterior snow. Mobile/device quality, final visuals, fishing, customer/hostile actors, the full economy and the Level 2 handoff remain open. The [one-camp design](docs/ONE_CAMP_DESIGN.md) explains what this preview reuses and what must stay separate.
