# Vehicle economy and later-world vehicles

**Selected direction:** make the snow truck an expensive earned machine with eight useful construction inputs and a small ongoing fuel cost. Add iron processing, shared mechanical components and an outside-camp oil source; reuse the same chains for nine distinct vehicles in the existing later worlds.

**Status:** these are authored design choices and arithmetic fixtures. They do not add workshops, oil deposits, controls, models or new worlds to the live game. Numerical bills, yields and fuel rates need playtests. The separately implemented fuel ledger has its own test and review receipts; this document does not promote its scope to integrated gameplay.

The machine-readable contract is [RESOURCE_CHAINS.json](RESOURCE_CHAINS.json); the fleet is [WORLD_VEHICLES.json](WORLD_VEHICLES.json). Exact source bindings and conflicting older wording are recorded in [SOURCE_AUDIT.md](SOURCE_AUDIT.md) and [SOURCE_AUDIT.json](SOURCE_AUDIT.json).

## What already exists, and what changes

The newly observed game head is Build14, `ea6e4896cc6692ee84b56f89e127feaa606eb370`. It already has a driveable truck, vehicle contact/docking code, outside cargo loss, inside salvage and a garage-time price choice. It still uses a fixed ten-ID cargo catalogue and integer counts, with no fuel or new iron/refinery balances. The source audit inspected those paths; it did not replay the APK or its media. Build14 reports limited destruction coverage and an open physical Galaxy Z Fold7 run. Those facts prevent treating this design package as a finished vehicle release. [Source evidence](SOURCE_AUDIT.json).

Keep saved `metal` as the ore ID. A versioned catalogue change can display **Iron ore** without granting bars or creating a duplicate `iron_ore` stock. Add `iron_bars`, `sheet_metal`, `crude_oil`, `mechanical_parts`, `drive_assembly` and `traction_kit`; the last displays **Mobility assembly** because it serves wheels, tracked drive, rail bogies and marine drive fittings. Reuse `coal`, `fuel`, `planks`, `blocks` and the previously authored `steel` product. Rubber, copper, batteries and electronics are not extra compulsory inventories.

Steel has a distinct job in blades, load-bearing frames and drive assemblies. Its new recipe is a branch from iron bars, not another compulsory stage before every sheet or part. Existing authored/in-flight direct ore-to-steel recipes retain their original version until explicitly migrated. Mechanical parts are a shared stock used by shutters, pumps, refining and mobility; drive and mobility assemblies recur across the fleet and paid equipment rebuilding. New items cannot enter customer orders or automatic worker jobs until their real source, handling and useful demand exist.

## Recipes and their producers

The exact batches below come from the JSON. All new quantities are unbalanced fixtures. Existing wood/stone conversions retain their current one-raw-bundle-to-one-product ratio. Coal is an explicit consumed smelting/refining input; engine fuel is not required to bootstrap these producers.

| Recipe | Inputs | Output | Producer |
|---|---|---|---|
| `saw_planks` | 1 Wood (`wood`) | 1 Planks (`planks`) | `saw_bench` |
| `dress_blocks` | 1 Stone (`stone`) | 1 Stone blocks (`blocks`) | `quarry_drill` |
| `smelt_iron` | 2 Iron ore (`metal`), 1 Coal (`coal`) | 2 Iron bars (`iron_bars`) | `coal_smelter` |
| `form_sheet` | 2 Iron bars (`iron_bars`) | 2 Sheet metal (`sheet_metal`) | `hand_metal_bench` |
| `machine_parts` | 2 Iron bars (`iron_bars`) | 2 Mechanical parts (`mechanical_parts`) | `hand_metal_bench` |
| `refine_steel` | 2 Iron bars (`iron_bars`), 1 Coal (`coal`) | 1 Steel (`steel`) | `steel_forge` |
| `assemble_drive` | 4 Steel (`steel`), 6 Mechanical parts (`mechanical_parts`), 2 Sheet metal (`sheet_metal`) | 1 Drive assembly (`drive_assembly`) | `assembly_bench` |
| `assemble_mobility` | 2 Steel (`steel`), 4 Mechanical parts (`mechanical_parts`), 2 Planks (`planks`) | 1 Mobility assembly (`traction_kit`) | `assembly_bench` |
| `refine_fuel` | 10 Crude oil (`crude_oil`), 1 Coal (`coal`) | 10 Fuel (`fuel`) | `coal_refinery` |

Mining stays outside the camp. Iron ore, coal, stone and slate have eligible external workfaces; the new crude deposit has an external **manual oil pump**. Manufacturing and the garage stay on fitting camp plots. Pumping is an authored hand-work action with real deposit custody and finite jobs, not a free inventory grant. It needs a reachable walking return route and no engine fuel. The coal-fired refinery then turns crude into usable fuel. Each mandatory source needs an attainable replenishment/recovery route; an empty tank, lost truck or destroyed workshop must not remove the only way to obtain fuel.

### Construction order that does not depend on vehicle fuel

The following is a declared material dependency proof, not a claim that those plots or routes have been built. Current camp expansion, storage, tools and safe-return prerequisites remain in force. Existing cooker/saw/quarry costs are preserved for the proof. Already-owned producers are never charged again.

| Build order | Producer | Construction inputs | Physical placement |
|---|---|---|---|
| 1 | `camp_cooker` | 12 Wood (`wood`), 8 Stone (`stone`) | inside expanded camp |
| 2 | `saw_bench` | 14 Wood (`wood`), 6 Stone (`stone`) | inside expanded camp |
| 3 | `quarry_drill` | 10 Wood (`wood`), 12 Stone (`stone`) | inside expanded camp |
| 4 | `coal_smelter` | 20 Planks (`planks`), 24 Stone blocks (`blocks`), 12 Stone (`stone`) | inside expanded camp |
| 5 | `hand_metal_bench` | 16 Planks (`planks`), 12 Stone blocks (`blocks`), 12 Iron bars (`iron_bars`) | inside expanded camp |
| 6 | `steel_forge` | 24 Stone blocks (`blocks`), 16 Iron bars (`iron_bars`), 8 Sheet metal (`sheet_metal`) | inside expanded camp |
| 7 | `assembly_bench` | 20 Planks (`planks`), 16 Stone blocks (`blocks`), 20 Iron bars (`iron_bars`), 12 Sheet metal (`sheet_metal`), 12 Mechanical parts (`mechanical_parts`) | inside expanded camp |
| 8 | `manual_oil_pump` | 16 Planks (`planks`), 12 Stone blocks (`blocks`), 12 Iron bars (`iron_bars`), 8 Mechanical parts (`mechanical_parts`) | outside camp reachable manual oil site |
| 9 | `coal_refinery` | 32 Stone blocks (`blocks`), 24 Sheet metal (`sheet_metal`), 16 Iron bars (`iron_bars`), 12 Mechanical parts (`mechanical_parts`) | inside expanded camp |

This profile deliberately makes the iron/steel/assembly/oil chain attainable in World1 before a new truck quote; it must not require a truck or travel to World3 to create the first truck. Desert and volcanic worlds still deepen mining, reinforced freight and forge work. This is an authored progression adaptation, not a previously observed World1 unlock.

This order establishes the first planks and blocks from wood/stone, then the first bars without bars in the smelter bill, then sheet/parts, steel, assemblies, the manual pump and the refinery. No new fuel-chain producer needs its own output to construct its first instance. The opening camp is not expanded to fit this equipment automatically; admit these later plots only with actual clearance, two usable bidirectional pedestrian exits, a centered furnace and the preserved initial scene scale.

## A substantial eight-input truck bill

This is the selected **new-quote fixture**; it is not a retroactive charge. Its material roles make the expense readable. The garage must already be complete, and actual sources/producers/return routes must make the full remaining obligation attainable before admitting the quote.

| Input | Count | Purpose |
|---|---:|---|
| Sheet metal (`sheet_metal`) | 80 | Body, cab and cargo panels |
| Iron bars (`iron_bars`) | 40 | Axles, bars and mechanical frame stock |
| Steel (`steel`) | 24 | Reinforced frame and horizontal cutting blades |
| Mechanical parts (`mechanical_parts`) | 40 | Steering, joints and tool mechanisms |
| Drive assembly (`drive_assembly`) | 1 | One complete drive unit |
| Mobility assembly (`traction_kit`) | 4 | Four wheel/mobility modules |
| Planks (`planks`) | 36 | Cargo floor and interior support |
| Fuel (`fuel`) | 60 | Funded initial operating tank; not construction waste |

**New garage fixture:** 64 Planks (`planks`), 48 Stone blocks (`blocks`), 24 Sheet metal (`sheet_metal`), 12 Steel (`steel`), 16 Mechanical parts (`mechanical_parts`). Sheet metal supports the shutter, steel the door frame and mechanical parts the opening mechanism. The old fence and its collision stay intact until a single atomic completed replacement installs the garage door. Existing paid garages and accepted/partially funded bills retain their original terms.

Future progression/target-tier curves may choose amounts before the quote is admitted. Freeze that complete bill, catalogue/denomination version, contribution escrow, target generation and starter-fuel allocation. Do not raise an accepted price because the player grew richer, advanced a level or already bought something. A paid replacement is a new legitimate generation with an attainable bill; cancellation/reload must not reroll debt.

### Raw-input arithmetic

These totals expand the declared recipe batches and reuse intermediate outputs. They are **legacy ledger bundles** for wood, stone, ore and coal; each legacy raw bundle displays ten raw units. Crude oil uses its own authored liquid-unit count. They are not mass, litres or identical physical units, and must not be added into one total. The script preserves any surplus output from a rounded batch.

| Scope | Wood bundles | Stone bundles | Iron-ore bundles (`metal`) | Coal bundles | Crude units |
|---|---:|---:|---:|---:|---:|
| New truck alone | 44 | 0 | 256 | 170 | 60 |
| New garage alone | 64 | 48 | 64 | 44 | 0 |
| All nine listed producer entries + garage + truck | 216 | 206 | 472 | 290 | 60 |

The last row is a material subtotal for constructing every listed production entry once; it excludes hearth, camp expansions, storage, unlisted route restoration and existing tools. Actual player cost omits already-owned producers. It proves arithmetic, not resource density, travel time, fun or affordability. More frequent common processed inputs and a slower drive-assembly milestone are intended to spread the goal across useful production; playtests must determine whether the fixture is enjoyable or excessive.

## Low fuel use with exact accounting

The selected test denomination is **120,000 tank subunits per fuel unit**, with a **60-unit tank**. Active propulsion consumes two subunits per millisecond, active powered tool use one, and simultaneous use three. At continuous use that is one fuel unit per minute of driving, per two minutes of tools, or per forty seconds combined. A funded full tank therefore represents sixty minutes driving-only or forty minutes simultaneous use in this fixture. Those are arithmetic bounds under continuous authenticated use, not a promise of route range or average play duration.

There is no drain while idle, docked, servicing, in menus, paused, backgrounded or closed. Refuelling explicitly transfers whole fuel units from an owned source while stationary with engine and tools stopped. Cargo fuel remains an ordinary unlimited resource; tank fuel is a separate operating balance. Returning to the garage transfers the entire ordinary cargo, including loose fuel, into the working all-resource warehouse. It leaves the operating tank aboard. If the destination is unusable, hold the whole cargo and retry when it works.

The new truck bill pays sixty fuel units into the tank in the same purchase transaction. That portion is not also recorded as consumed construction material. Old accepted quotes lacking that field finish on their old terms with an **empty** tank; old paid trucks migrate with empty tanks and preserve HP, cargo, generations and ownership. A new fuel requirement never invents a free tank or retroactive debt.

Build14 currently permits truck repurchase only after ordinary cargo salvage is cleared. **Keep fractional tank estates separate:** they can be claimed only into a live tank, so a paid replacement must remain possible while that fuel estate exists. Combining those balances would create a deadlock in which no live tank can receive fuel and no replacement can be bought.

At zero fuel, propulsion and powered tools stop safely; the vehicle persists with HP and cargo. The driver can exit, make/bring fuel using the manual chain and return. The stranded vehicle remains subject to ordinary attack; this design does not grant safe transport or immunity. Outside destruction loses remaining ordinary cargo and tank fuel exactly once. Inside destruction retains typed cargo salvage and a separate exact fractional fuel estate, recoverable into an eligible live tank without rounding. Personal driver inventory follows its separate preserved-inventory recovery.

Fuel authorization alone does not move a vehicle or land a strike. The trusted world adapter must authenticate each active interval, debit it before motion/tool work, execute each resulting grant once and commit the coupled physical/resource state durably. Native receipts and counts are covered by the component review; actual blocked motion, sustained controls, pause/resume and contact require game integration evidence.

## Nine useful later-world vehicles

Each is an authored proposal tied to an existing world, not a new level or world unlock. Every vehicle gets recurring existing-resource work after its first project. Construction profiles use the same shared material graph and funded sixty-unit tank fixture; the JSON keeps each exact bill. Route, garage/dock, clearances, source availability and a return anchor determine eligibility.

| World / task | Vehicle and locomotion | Working tool | Recurring purpose |
|---|---|---|---|
| 2 — Forest and lakeshore / T44 | **Timber Forwarder** — Articulated six-wheel forwarder | Hydraulic timber grapple and guarded saw | Cut and collect reachable timber on forest lanes; Load mixed wood, planks and ordinary construction supplies for recurring bridges and repairs |
| 3 — Desert canyons / T45 | **Canyon Breaker** — Low crawler with two broad tracks | Front hydraulic rock breaker and four stabilizer feet, one front and one rear per side | Break eligible stone, slate and ore workfaces; Carry masonry and reinforcement stock to protected freight routes and paid repairs |
| 4 — Underwater refuges / T46 | **Reef Salvager** — Sealed dry-cab four-wheel salvage crawler | Telescoping lift and grapple reaching flooded workfaces | Lift marked metal/fuel salvage from flooded workface to protected loading dock; Carry blocks, planks and steel for dry habitat/pump restoration and repeat supply work |
| 5 — Sky islands / T47 | **Skybridge Carrier** — Rail-guided carrier with captive under-rail rollers | Folding freight crane | Carry planks, steel and ordinary supplies across restored bridge links; Lift freight to fixed platforms for repeating route maintenance and resupply |
| 6 — Volcanic forge / T48 | **Forge Hauler** — Heat-shielded six-wheel ore hauler | Wide front mineral scoop on twin short hydraulic arms | Collect eligible ore and coal from protected extraction aprons; Supply steel/blocks/slate to repeated forge, causeway and equipment repair projects |
| 7 — Swamp / T49 | **Marsh Skiff** — Shallow-water pontoon cargo skiff | Guarded twin stern drives and folding cargo winch | Ferry timber, fish and ordinary supplies over marked cargo crossings; Winch supply bundles onto stable landings for recurring boardwalk/platform repair |
| 8 — Ruined settlements / T50 | **Ruin Reclaimer** — Compact four-wheel demolition loader | Hydraulic jaws and rubble bucket | Break eligible abandoned rubble and recover marked salvage; Move blocks, planks, slate and steel to repeated gate/workshop restoration |
| 9 — Underground mines / T51 | **Mine Mole** — Low-profile rail service locomotive | Horizontal front cutting drum and open ore hopper | Mine eligible ore, coal, stone and slate at rail workfaces; Deliver steel, blocks and repair supplies to recurring support/light/lift jobs |
| 10 — Alien frontier / T52 | **Relay Rover** — Articulated six-wheel service rover | Precision lifting arm and stabilizing outriggers | Haul and install finite serialized relay components between restored worksites; Continue hauling ordinary construction, fuel and repair stocks after network completion |

The current concept contract is six static views: front, rear, both sides, three-quarter and one at-work view. Full turning, overhead clearance, service/docking and complete motion cycles are separate pending native-production evidence, not additional concept-sheet requirements in this iteration. Canyon Breaker uses the selected front-right cab and four stabilizer feet; Forge Hauler has a wide front scoop on twin short arms; Mine Mole has a horizontal cutting drum and open ore hopper. Ruin Reclaimer’s partly open travel jaw is an illustrative stowed pose; its working jaws must close onto supported rubble. These stills do not prove complete tool transitions or clearance.

The Reef Salvager remains on protected dry dock/habitat routes; its arm reaches the flooded workface. Neither people nor pets acquire compulsory swimming or oxygen meters. The Skybridge Carrier stays captive to restored fixed bridges/rails/lifts and never grants free flight. The Marsh Skiff serves authored marked crossings and stable landings. Mine Mole uses rails/lifts; conveyor belts still carry goods, not people.

Relay Rover’s forward authored design is a **portable serialized relay module**, carried on its deck and installed at a restored worksite. It follows the ordinary outside-vehicle cargo-loss rule: a destroyed truck loses the module, with no protected-item exception, salvage of that lost instance or free return to storage. The associated restored worksite can fabricate a **paid replacement for the same objective serial** using attainable ordinary shared materials. A new instance generation replaces the proven-lost one; it does not add an objective or reset installed progress.

Keep one active uninstalled instance per objective serial across every custody location and replacement reservation. Successful installation consumes that instance and writes a permanent one-install tombstone, so retries cannot install twice or repeat a reward. An interrupted lift retains the actual precommit source/transfer owner, or the committed installed result; it cannot create both. The counted cargo and its serial-to-custody record must commit together. Ordinary site repair, replacement materials and manual return must remain attainable without the missing module or truck.

The replacement recipe is **pending**: sheet metal, steel and mechanical parts are sensible shared-material candidates, not an implicit approved bill. Its exact quantities and paid production transaction still require feasibility and balance evidence. The module cannot become a currency, sellable farming output or input to its own replacement. Source evidence says only finite project object; inspect and explicitly migrate any existing portable/structural save identity rather than silently reclassifying it. The earlier fixed-site alternative is retained as superseded history in the source audit. This authored selection aligns with the carried module and installation concept views; its runtime custody and recovery are still unimplemented.

The fleet inherits the selected unlimited mixed-resource cargo/warehouse and loss policy. Safe default camp travel stops working tools; deliberate eligible-hostile defense still needs the real clearance/target rules. Docking, refuelling, service and unloading stop tools. Incidental contact cannot destroy friendly people, animals or owned buildings. The older blanket camp-blade prohibition remains an explicit source conflict to resolve in the actual game.

The live adapter needs more than extra catalogue keys. `configure`, `payment`, `vehicle_repurchase`, `vehicle_pay_repair`, `_move_vehicle_goods` and restore still assume raw/planks/blocks/meal/money dictionaries. `field_progression.price_text` iterates eight IDs, converts counts to native integers and multiplies all except planks/blocks by ten. Replace those coupled dispatch and formatting paths with exact typed custody and per-resource denominations; otherwise new bills disappear from the HUD or cannot be paid, and large mixed counts or fuel quantities can be misrepresented. [Pinned source excerpts](SOURCE_AUDIT.json).

## What is still missing before integrated acceptance

| Priority / owner | Required next action | Evidence that closes it |
|---|---|---|
| 1 — Catalogue/save owner | Reconcile the Build14 head, raw bundle denomination, metal display, new IDs and all custody locations. Preserve legacy quotes/recipes/paid vehicles; migrate tanks empty. | Old-save and in-flight contribution/production/haul/estate round trips; staged rollback; exact counts and no extra debt/value. |
| 2 — Resource/world owner | Build external iron/coal/oil workfaces, manual pump, safe walking return and replenishment under actual progression. | Zero-fuel/zero-new-material start can build and refuel using genuine source contacts; lost machinery and blocked route recovery. |
| 3 — Production/economy owner | Implement smelter, metal bench, forge, assembly and refinery with frozen recipe batches, input escrow and paid construction. | Full idle/run/output-blocked/interrupted/resumed cycles; no output before spend, duplication, hidden fuel loop or unreachable quote. |
| 4 — Vehicle/world adapter owner | Bind fuel use, actual driving/reverse/braking, separate tool control, eligibility/target contact and zero-fuel stopping. | Continuous real driving/tool sessions, stalls, multi-touch, pause/background, reload and adversarial duplicate grants; controls remain usable. |
| 5 — Camp/lifecycle owner | Couple atomic fence replacement, full-hull docking, operational all-resource warehouse, paid garage/storage/furnace recovery and driver exit. | Breach, fire/disabled producer, warehouse destruction, stuck bay, mixed-cargo unload, inside/outside wreck and full recovery without value loss/duplication. |
| 6 — World/asset owners | Fit all nine locomotion/tool designs to actual route, cabin, pet/driver staging, contact, return and later useful jobs. | Source-bound multi-angle native views and complete motion/use cycles; World4 dry habitats, World5 fixed flight-free links, World9 rail safety and World10 serialized outside loss, paid same-objective replacement and one-install custody. |
| 7 — Persistence/performance owner (T14) | Bind complete-world atomic save and measure long-session journal growth; compact with retained idempotency and destruction/installation tombstones. | Crash injection, long-history reload/size/timing measurements and proven conservation across checkpoints. Full event history alone is not production-scale evidence. |
| 8 — Balance, device and independent critics | Tune costly mixed bills and low fuel around actual material density/route time; inspect physical target devices and readable HUD. | Reachable free-player progression and recovery sessions; physical Fold7 controls/performance, audio playback and all mandatory source-bound reviews. |

The broader gameplay backlog also retains full actor/structure destruction coverage, paid recovery routes, unlimited useful survivor work and hunting, all seven pets with real attacks plus specialties, named-camp raid targeting with the existing active-time warning, self-service stocked counter and cash custody, full-body animation/contact, and the unresolved overall level-count plan. Original T01–T70 remain unchanged; no T71–T80 definitions are invented here.

## Reproduce the bounded material check

From the repository root:

```bash
python Docs/Production/VehicleEconomy/2026-11-27/verify_economy.py
```

The saved run passed **84/84 declared graph checks**. [evidence/economy_checks.json](evidence/economy_checks.json) binds the exact JSON and checker hashes, batch expansions and negative examples. It rejects a circular bar/sheet recipe, an unavailable first smelter, missing crude source and an unregistered item. It verifies that both shared assemblies have multiple uses and that each new vehicle tank is paid. Physical reachability, runtime integration and numerical balance remain untested by this check.

Independent review must inspect these exact files and the separately frozen component/art evidence. Any missing mandatory runtime, model, motion, audio or device evidence blocks the relevant acceptance; an authored static concept or passing ledger test cannot close it.
