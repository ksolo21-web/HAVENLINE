# Resource stock and processing-machine map

This crosswalk preserves the selected economy identities. It adds no quantities, prices, compulsory intermediate stocks or runtime approval. Resource icons represent stocks; the single pictured object does not establish a physical unit or yield.

| Resource ID | Display | Source / processor | Input families | Useful destination |
|---|---|---|---|---|
| `wood` | Wood | Registered trees and timber sources. | — | planks; bootstrap producers; furnace recovery |
| `stone` | Stone | Registered stone deposits. | — | blocks; bootstrap producers; recovery construction |
| `metal` | Iron ore | Registered ore mining. | — | iron_bars; retained legacy raw bills |
| `coal` | Coal | Registered coal mining. | — | iron smelting; steel refining; oil refining |
| `steel` | Steel | steel_forge | iron_bars, coal | blades and reinforced chassis; drive assemblies; traction assemblies |
| `slate` | Slate | Registered slate deposits. | — | weatherproof roofs; protected work surfaces |
| `planks` | Planks | saw_bench | wood | garage structure; cargo floor; traction assembly; producer frames |
| `fuel` | Fuel | coal_refinery | crude_oil, coal | funded vehicle tank; ordinary refuelling; eligible future powered-work jobs |
| `meat` | Meat | Retain current hostile-wolf drops and select Tundra Stag hunting; owned companions are never valid targets. Preserve all already-owned generic meat. Boar remains art reserve. | — | Cooked meal service and explicit rescue/roost supplies. |
| `meal` | Meal | camp_cooker | meat | Customer service and selected named supply objectives. |
| `fish` | Fish | Authored automatic fishing action. | — | Whole cooked-fish service branch. |
| `cooked_fish` | Cooked Fish | existing_intake_and_cooker_T16 | fish | Eligible customer orders. |
| `wheat` | Wheat | Registered crop harvesting. | — | Direct bread-like production input. |
| `bread` | Bread | existing_wheat_processor_T19 | wheat | Eligible customer and mixed food orders. |
| `hide` | Hide | Selected Tundra Stag byproduct; source/drop flags and quantities require authored evidence. | — | Harness construction and elective retrofitting for visible working equipment. |
| `fur` | Fur | Selected winter-stag byproduct or ordinary earned supply order; no owned-pet harvesting. | — | Specific cold-work clothing and shelter fittings. |
| `money` | Cash | Exactly-once fulfilled service orders; custody in till, pocket or house. | — | Station improvements, mechanical add-ons, transport construction/services and optional efficiency specialization. |
| `cargo` | Cargo | Typed goods grouped for physical transfer. | — | Preserve transport custody and legibility. |
| `iron_bars` | Iron bars | coal_smelter | metal, coal | sheet metal; parts; steel; axles and producer frames |
| `sheet_metal` | Sheet metal | hand_metal_bench | iron_bars | vehicle body panels; garage door; refinery casing |
| `mechanical_parts` | Mechanical parts | hand_metal_bench | iron_bars | drive assemblies; traction assemblies; garage shutter; oil pump/refinery |
| `drive_assembly` | Drive assembly | assembly_bench | steel, mechanical_parts, sheet_metal | vehicle drive systems; powered lift/hauler rebuilds |
| `traction_kit` | Mobility assembly | assembly_bench | steel, mechanical_parts, planks | wheel or track modules; captive rail bogies; marine propulsion fittings |
| `crude_oil` | Crude oil | manual_oil_pump | — | fuel refining |
| `blocks` | Stone blocks | quarry_drill | stone | garage foundations; smelter/refinery bases; safe route structures |
| `premium_gems` | Gems | Server-authoritative fixed disclosed grants/purchases. | — | Fixed optional catalogue content/value, separated from challenge and mandatory progress. |
| `relay_component` | Relay component | finite_relay_recovery_replacement_worksite_future | — | Complete the final relay connection under T52. |

## Existing processing references

| Route | Preserved selected art |
|---|---|
| Wood → planks | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/saw_station.png` |
| Stone → blocks | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/quarry_drill_station.png` |
| Meat → meal | `Docs/Design/RenderArchive/2026-11-23/selected/equipment/cooker_processor.png` |
| Fish → cooked fish | Existing `intake_machine.png` and `cooker_processor.png`, as selected under T16 |
| Wheat → bread | `Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/selected/world-wheat-processor.png`, pinned art commit `a868ae89cdf2f120b478aa0a48fff35e09cc465c` |

## Industrial dependency order

Saw and quarry outputs build the coal smelter. Smelted iron bars enable the hand metal bench. Its sheets enable the steel forge, and its parts enable the outside-camp manual oil pump and coal refinery. The assembly bench combines useful processed families into drive and mobility assemblies. The pump and refinery remain usable before the first vehicle fuel exists.

The latest iron route is **iron ore (`metal`) + coal → iron bars → sheets / parts / steel**, retaining the old saved ore key. Vehicle-economy fixture quantities remain unbalanced.

Cash comes from eligible service transactions, and Gems belongs to its separate optional premium system; neither has a resource-processing machine. Cargo is custody presentation. The relay object belongs to one finite objective serial and its restored worksite, not an endless manufacturing wallet.

Hide and fur already have harness, clothing and shelter uses. Art variants such as species cuts, dried meat, fillets and split firewood remain preserved variants/reserve concepts unless separately selected. Their existence does not introduce mandatory extra processing.
