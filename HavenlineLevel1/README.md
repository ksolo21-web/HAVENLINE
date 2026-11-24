# Havenline Level 1 replacement

**Branch checkpoint: source, assets and reviewed furnace purchase behavior. Not a release or the full Level 1 playtest.** This project lives separately from `HavenlineGodot/` during replacement work. Nothing in the canonical project is deleted, and no workflow or default branch is changed by this checkpoint.

Base: `codex/havenline-sequential-task-01` at `f74a84a2a288ab3d3935fba7a6cb9b975c2df239`. The opening source is the independently retested V8-derived strict wood repair. It preserves the 3-wood price, rejects an inactive or unbound furnace pad without taking wood, and preserves the receipt across a clean restart. Independent scoped checks: 29 writer, 3 cold-reader, 10 adverse/eligibility, and 7 scripted movement/input checks. No live rendered or device pass, typed fish transfer, customer, enemy, or Level 2 unlock claim.

## Run this checkpoint

From the cloned repository root, run `python3 HavenlineLevel1/tools/hydrate_assets.py` (Python 3.11 or later). It verifies all four studio files and restores the exact furnace file from three Git-tracked pieces. No login, external download or alternative art is needed. Then import `HavenlineLevel1/project.godot` in Godot 4.7.2. For headless import in a disposable environment, run `godot --headless --path HavenlineLevel1 --editor --import --quit`. The full live, rendered and on-device verification remains separate. The Godot scene runs the revised opening only, not the full Level 1 progression.

The one-camp replacement design and ownership boundaries are in [ONE_CAMP_DESIGN.md](docs/ONE_CAMP_DESIGN.md).

## Next integration slice

Keep the approved river and forest. Use the revised camp as the single active camp in this separate Level 1 project. Preserve the old project and original assets. First resolve the terrain bank and floor-height seam; then test both gates through ordinary input, fishing access, and loaded return routes on the exact integrated build. Do not enable a second camp ledger, a second fence network, or paths painted over exterior snow. Keep later tasks and the default branch untouched until independently verified in scope.
