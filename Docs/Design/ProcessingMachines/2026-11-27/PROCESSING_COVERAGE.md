# Havenline resource processing — render coverage

## Result

The selected industrial expansion needs **six new machine families**. The existing cooker, saw, quarry, fish-line and wheat-processing references should be reused. Each new machine belongs to a producer already named in the vehicle-economy contract; this plan adds no mandatory material or recipe.

This is an art-planning document. It does not claim that these machines, animation cycles, recipes, plots, conveyor sockets or save behavior are implemented in the game. Source recipe quantities below are engineering fixtures copied unchanged, not balanced production values.

| New machine | Input | Output | Design that makes its job readable |
|---|---|---|---|
| Coal smelter | Iron ore + coal | Iron bars | Tall stone-lined chamber, separate ore chute and coal drawer, bar molds and cooling tray |
| Metal forming and parts bench | Iron bars | Sheet metal **or** mechanical parts | One hand-driven workbench with rollers and a parts die; separate flat sheet tray and parts bin |
| Steel refining forge | Iron bars + coal | Steel | Broad low forge, crucible cradle, bellows, protected cooling rack; distinct from the ore smelter |
| Vehicle assembly bench | Steel + parts + sheet metal; or steel + parts + planks | Drive assembly; or mobility assembly | Reinforced table, small gantry hoist, assembly jig, separated component bays and wide output cradle |
| Manual oil pump | Reachable outside-camp crude deposit | Crude oil | Hand lever, visible reciprocating piston, sealed drum and a walkable pickup position |
| Coal-fired refinery | Crude oil + coal | Fuel | Compact still, condenser, separate crude coupling and coal drawer, clean-fuel can filling bay |

The metal bench has two recipes. The assembly bench has two recipes. Their different output jobs do not create additional mandatory buildings.

## Existing machine references to retain

The pinned render catalogue identifies the original assets at commit `a868ae89cdf2f120b478aa0a48fff35e09cc465c`:

| Existing machine or line | Resource route | Existing reference |
|---|---|---|
| Camp cooker | Meat → meal | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/cooker_processor.png` |
| Saw bench / lumber equipment | Wood → planks | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/saw_station.png`; `lumber_mill.png` |
| Quarry drill | Stone → blocks | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/quarry_drill_station.png` |
| Fish line | Whole fish → cooked fish | Existing intake, cooker and selected conveyor references |
| Wheat food processor | Wheat → bread | `Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/selected/world-wheat-processor.png` |
| Harvesting support | Wheat acquisition | Same selected directory: `world-wheat-harvester.png` |
| Workshop / cookhouse / storage | Existing building and work context | Same selected directory and original equipment archive; no automatic new recipes from their appearance |

Cooker, saw and wheat processor sheets were visually inspected during this planning task. Quarry reference existence and identity are grounded in the pinned render catalogue; its full image was not visually re-reviewed here. The catalogue's original scores, including historical 9.4 equipment and 9.8 wheat-processor scores, remain historical. Reuse is not a new final approval.

## Exact industrial recipe fixtures

| Recipe | Inputs | Output | Producer ID |
|---|---|---|---|
| Smelt iron | 2 `metal`, 1 `coal` | 2 `iron_bars` | `coal_smelter` |
| Form sheet | 2 `iron_bars` | 2 `sheet_metal` | `hand_metal_bench` |
| Make parts | 2 `iron_bars` | 2 `mechanical_parts` | `hand_metal_bench` |
| Refine steel | 2 `iron_bars`, 1 `coal` | 1 `steel` | `steel_forge` |
| Assemble drive | 4 `steel`, 6 `mechanical_parts`, 2 `sheet_metal` | 1 `drive_assembly` | `assembly_bench` |
| Assemble mobility | 2 `steel`, 4 `mechanical_parts`, 2 `planks` | 1 `traction_kit` | `assembly_bench` |
| Refine fuel | 10 `crude_oil`, 1 `coal` | 10 `fuel` | `coal_refinery` |

Preserve `metal` as the saved ore ID; its selected display name is Iron ore. Preserve `traction_kit` as the authored component ID; its display name is Mobility assembly. Neither display label justifies a duplicate stock balance. Coal and crude are consumed as recipe inputs; the machines do not require engine fuel to bootstrap.

The legacy raw counts are bundles displaying ten raw units per count. New bars, sheets and components use their authored count. Crude and fuel use abstract liquid units. These numbers are not dimensions, litres, mass or the count of visible props on a rendered tray. Bread/fish quantities are not invented here.

## Construction path and recovery

The supplied material graph starts with manually reachable wood, stone, ore, coal and slate. The cooker, saw and quarry establish planks and blocks. The first smelter uses planks, blocks and stone, so it does not require the iron bars it is meant to make. Bars then make the metal bench possible; that bench supplies sheets and parts. Steel, assemblies, the manual pump and the refinery follow.

The material check verified all nine listed producer bills in declared order and every source recipe's inputs. All six checks in `MATERIAL_GRAPH_CHECK.json` passed. This proves the declared graph has a fuel-free construction path; it does not prove physical placement, actual walking routes, source regeneration, available camp space or balance.

The oil pump stays outside camp on an eligible reachable crude deposit. The refinery and manufacturing equipment occupy later fitting camp plots. These renders must not expand the initial camp, move the centered hearth or obstruct either bidirectional pedestrian gate. A truck, a working engine, later-world travel or a vehicle-only crossing cannot be required to make the first fuel.

Manual input and output positions stay usable even when conveyors have not been built or are damaged. Conveyors move the same typed goods between designated sockets; they do not mint resources, change recipes or become compulsory first-use prerequisites. Already-owned producers retain ownership and are not charged again by a new truck quote.

## Ports and complete action intent

`PROCESSING_MACHINE_MAP.json` specifies each machine's fixed inputs, outputs, worker positions and distinct idle, working, blocked-output and damaged/jammed behavior. For the static render task those entries are animation requirements to carry into implementation, not evidence of working motion.

The resource cue belongs at the physical port: ore or bar feed, separate coal drawer, fluid coupling, finished sheet tray, parts bin or assembly cradle. Both material shape and a clear port symbol should identify the resource; color alone is insufficient. Worker access cannot pass through a hopper, belt or hot chamber. Empty containers in the imagery are presentation props unless an established inventory contract says otherwise.

When output is full, input consumption must stop before a new batch commits. Finished owned output may remain in its reserved safe tray or vessel. Damage must stop actual work and show a believable failure location while conserving the job's precommit or postcommit custody. The latest gameplay destruction/rebuy rules control recovery; this art plan does not substitute older free-repair wording.

## Bounded exclusions

Slate already has direct roof and work-surface uses. Hide goes to harness construction; fur goes to cold-work clothing and shelter fittings. Their visual existence does not create slate-tile, leather or cloth inventories. The selected wheat route has no mandatory flour stage. Species meat cuts, dried foods and split firewood are preserved art variants or reserve concepts unless an introducing owner selects their existing useful role.

Gems remain optional currency, not a factory output. Relay components are finite project objects used by the final connection; no manufacturing recipe or relay factory is established by the inspected plan. Do not add compulsory rubber, copper, battery, electronic, waste or petroleum-byproduct stocks to the vehicle chain.

## Acceptance and next action

The next action is to generate the six new machine sheets using the original equipment style and the already-selected new resource forms, then submit the actual sheets to a separate critic. Preserve each generated original, rejected revision, exact prompt, ordered source images and final selected alias. Every final static-art claim must identify its exact file and reviewed scope.

The current forward reference standard requires each applicable reference-sensitive score at least 9.9, with any stronger exact-10 rule retained. Missing evidence blocks approval. A machine sheet can pass only its static concept scope; it cannot approve a native mesh, footprint, rig, cycle, touch target, runtime economy or device performance.

The static acceptance checklist is in `ACCEPTANCE_CHECKLIST.json`; current pending work is in `CHECKPOINT.json`.

## Source custody

Exact local source identities and SHA-256 hashes are recorded in `PROCESSING_MACHINE_MAP.json`. Principal sources:

- `Docs/Production/VehicleEconomy/2026-11-27/RESOURCE_CHAINS.json`
- `Docs/Production/VehicleEconomy/2026-11-27/ECONOMY_DESIGN.md`
- `Docs/Production/Completeness/2026-11-27/PROGRESSION_ECONOMY_GAPS.md`
- `Docs/Production/ReferenceRefresh/2026-11-27/RENDER_CATALOGUE.md`
- `Docs/Production/T05/FROZEN_SCOPE.md`
- `Docs/Production/REFERENCE_ACCEPTANCE_STANDARD.md`
- Existing `source-equipment-coverage.json` under the November 26 conveyor references, used as a historical art inventory rather than as authority over newer vehicle recipes.
