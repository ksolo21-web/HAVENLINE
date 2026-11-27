# Havenline: stakes and resource-value audit

**Status: SOURCE AUDIT + PROPOSED DESIGN; no runtime changes, playtest, approval, or balance signoff.**

Audit date: 2026-11-27. Plan base: 9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c. Latest verified build receipt inspected: game source 989edd9283148e9f712387fb937ea36038cbd9d2 (Build 11, trial/world-one-expansion-2026-11-26). Render source: a868ae89cdf2f120b478aa0a48fff35e09cc465c. The build receipt is an inspected historical pin, not a claim that a moving branch has no later changes. The whole-game target remains Levels 1–100; authentic task definitions are T01–T70, with T71–T80 undefined.

## 1. Direct answer

**The current foundation has forgiving combat risk, but the complete whole-game stakes contract is not frozen. Every resource is not yet proved worthwhile.** The plan establishes strong fairness constraints and requires physical resources, production and service, yet a complete source-to-use economy and failure/recovery specification remains work to do.

At the inspected Build 11 source, the player can take damage outside camp. At zero HP, they fall, return to the safe start, and recover full HP. The inspected down/reset path does not debit carried materials, saved stock, paid plots, cash or companions. Camp is a sanctuary and gradually heals the player. Consequently, the current demonstrated-by-source cost is interruption and return travel; it is not established cargo loss, permanent death, colony destruction, hunger or a paid revive. This is code inspection, not a new runtime test. [F1][F2][F3]

There is a second existing form of loss: loose field drops have a lifetime in played simulation seconds. That affects goods not yet collected; it is distinct from losing already owned cargo on defeat. The source snapshots remaining drop life and advances timers using simulation time; _step_drops removes expired loose drops and _place_drop removes the oldest loose drop when the cap is reached. This is not evidence of an offline-loss clock. Runtime expiry/cap behavior still needs play verification. [F1][F3]

The more serious design gap is that some collectibles do not yet lead to a compelling payoff. Coal, slate and metal are real raw inventory IDs in the inspected foundation but have no spend or processor sink in the reviewed 13 build offers and three processor contracts. Planks and blocks are real outputs that can fill storage and satisfy the opening completion receipts; a downstream construction or sale sink is not present in those reviewed contracts. Cash is visibly exchanged at the counter, but the inspected settlement ledger records a meal served, not a spendable cash wallet. The full earned-money-to-reinvestment loop remains unproved. [F4][F5][F6][F7][F8]

## 2. Evidence scope and authority

### Source index

| Ref | Exact source and useful anchor |
|---|---|
| P1 | [BUILD PLAN V2 at plan base](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/HAVENLINE_BUILD_PLAN_V2.md), core loop, automatic resource/tool/actor/animation contract, Economy, T01–T80 table, audio supplement |
| P2 | [RESOURCE_ACTION_REGISTRY.json](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/RESOURCE_ACTION_REGISTRY.json), resources and future_resource_rule |
| P3 | [RESOURCE_TOOL_ACTOR_STANDARD.md](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md), human-companion permissions and no generic fallback |
| P4 | [TASK_REFERENCE_MATRIX_T01_T80.json](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.json), rows T13, T16–T23, T31–T40, T44–T53, T63–T64 |
| P5 | [T13 IMPLEMENTATION_BLUEPRINT.md](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/T13/IMPLEMENTATION_BLUEPRINT.md), PerformanceWindow, forbidden inputs, bounded escalation/recovery |
| P6 | [REFERENCE_ACCEPTANCE_POLICY.json](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/REFERENCE_ACCEPTANCE_POLICY.json), final_acceptance, interpretation, evidence_requirements |
| P7 | [RAW_REFERENCE_AUDIT.md](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/RAW_REFERENCE_AUDIT.md), RF05/RF10/RF11 and unlimited logical carry boundary |
| P8 | [LATEST_BUILD_EVIDENCE.json](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/LATEST_BUILD_EVIDENCE.json), verified Build 11 source identity |
| F1 | [field_opening.gd at 989edd9](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_opening.gd), _player_hit, zero-HP reset branch, _advance_camp_heal, _wolf_defeated |
| F2 | [field_encounters.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_encounters.gd), hero_safe, advance, wave/spawn/return handling |
| F3 | [field_lifecycle.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_lifecycle.gd), DROP_LIFETIME_SECONDS, snapshot, safe_start, _restore_actor, advance |
| F4 | [field_inventory.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_inventory.gd), KINDS/TITLES, worker_payment, _pay_from, snapshot/validation |
| F5 | [field_progression.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_progression.gd), OFFERS, MACHINES, UNITS_PER_BUNDLE, LINES, survivor plot |
| F6 | [field_logistics.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_logistics.gd), RAW, PRODUCT, STORE, LANES, rack, receiving_space, valid |
| F7 | [field_settlement.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_settlement.gd), EMPTY, WORKER_LOAD, WORKER_LIMIT, _original_receipts |
| F8 | [field_settlement_loop.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_settlement_loop.gd), serve, cancel_cooking, collect_meal, collect_worker_meal |
| F9 | [field_counter.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_counter.gd), MONEY, _serve, _clear_presentations |
| F10 | [field_processors.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_processors.gd), wood/stone stations, sync_outputs |
| F11 | [field_conveyors.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_conveyors.gd), Products, _demand, _launch, _arrive, present |
| F12 | [field_hud.gd](https://github.com/ksolo21-web/HAVENLINE/blob/989edd9283148e9f712387fb937ea36038cbd9d2/HavenlineLevel1/field_hud.gd), settlement_status: cash display maps to journal.served |
| R1 | [Base resource delivery manifest at render pin](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23/delivery-manifest.json), 13 sheet IDs, coal_status, cooked_food_status, approval boundaries |
| R2 | [Expansion resource delivery manifest](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23-expansion/delivery-manifest.json), 20 sheet IDs and scope_status |
| R3 | [Source/equipment coverage](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23-expansion/source-equipment-coverage.json), historical inspection_scope, proposed output mapping, undefined_recipe_fields, excluded_unestablished_outputs |
| R4 | [Current render source register](https://github.com/ksolo21-web/HAVENLINE/blob/9d10c45a8bd46aeb6ab1b4009e87538c4796ef1c/Docs/Production/ReferenceRefresh/2026-11-27/RENDER_SOURCE_REGISTER.json), pinned archives/selected_images and limits |

A source-derived design observation is not runtime acceptance. Static art does not prove yield, recipe, damage, capacity, AI, economy, animation or continued usefulness. Older HavenlineGodot source is historical evidence; do not merge its wallet or resource IDs into the new foundation without an explicit migration.

### Existing commitments

The approved plan already forbids energy walls, mandatory payment, fake discounts, hidden spend-driven difficulty and an intentionally miserable free path. It requires realistic Level 1–100 completion at $0, retained advertised purchase value, one primary premium currency, and permanent transparent VIP. Challenge Director receives behavioral observations, not purchase, VIP or premium-wallet data. [P1][P5]

T13 contains a bounded difficulty decision contract. It may consume defeat/down/recovery observations where the activated runtime emits them; it does not establish a death penalty, resource theft, hunger, gear decay or colony wipe mechanic. The audio plan mentions defeat/recovery and healing cues, but cue names are not gameplay rules. [P1][P5]

T08 preserves unlimited logical player inventory separately from finite rendered stacks and the worker-capacity contract. Do not introduce a player encumbrance penalty, finite pack cap or forced cargo discard as an unapproved economy fix. [P4 T08][P7]

## 3. Current source observations and gaps

| Area | Existing source evidence | What remains unproved |
|---|---|---|
| Damage and sanctuary | _player_hit rejects attacks in camp; damage reduces HP outside; camp healing is explicit. [F1][F2] | Full encounter fairness, warning readability and recoverability under actual play. |
| Player defeat | Fall interrupts activity and relocates to safe_start with full HP; reset keeps living enemies' current HP. [F1] | Whole-game rule for losses, rescue alternatives, late-region checkpoints and repeated defeat. |
| Inventory on defeat | No inventory/material debit in inspected down/reset path; cancel_cooking preserves committed hopper stock and machine work. [F1][F8] | A formally approved player-facing guarantee and regression coverage across every failure/save path. |
| Loose field drops | Drop lifetime and snapshot remaining time exist, using played simulation time. [F3] | Runtime expiry/cap behavior and clear distinction between abandoned loose loot and owned cargo. |
| Camp attack | Reviewed encounter code treats camp as sanctuary. [F2] | Raid damage, repair cost, theft, siege or destroyed buildings are not demonstrated by this source. |
| Survivors funding plots | Rescued worker may contribute actual worker_load through the shared _pay_from validator; Progress.LINES are explicitly excluded. [F4][F5] | Complete all-task parity, spending priorities, reserve rules, cash authority and conveyor-purchase parity. |
| Worker capacity | WORKER_LOAD supports six raw kinds; WORKER_LIMIT is expressed as 500 raw units / ten-unit bundle in source. Validation applies by kind. [F7] | Do not claim total or mixed-capacity parity without tracing the job-selection and capacity logic; no broad whole-game proof. |
| Progression spending | 13 OFFERS consume wood/stone/meat. Survivor wood plot is a separate milestone. [F5] | Later materials, cash, processed outputs and whole-game task costs/yields. |
| Customer transaction | One real meal is consumed, served count increases, a cash mesh exchanges, then presentation clears. [F8][F9] | Persisted spendable earned-cash balance and reinvestment sink. The mesh is not a wallet proof. |
| Processed output | wood→planks, stone→blocks, meat→meal; capacity/backpressure accounting exists. [F6][F10][F11] | Plank/block downstream use beyond storage and opening milestone receipts. |
| Late regions | T44–T52 cover forest through alien and must register new resources/actions; visual packs often do not freeze hazards or recipes. [P2][P4] | Authored pressure/recovery/source/demand/surplus contracts per region; Level 1 evidence cannot certify Levels 11–100. |

### Exact source excerpts

F4, worker_payment / _pay_from:

    func worker_payment(id: String, kind: String, amount: int) -> bool:
        if not settlement.rescued or id in Progress.LINES: return false
        return _pay_from(settlement.worker_load,id,kind,amount)

    func _pay_from(stock: Dictionary, id: String, kind: String, amount: int) -> bool:
        if amount <= 0 or not offer_open(id) or not costs[id].has(kind) or amount > costs[id][kind] - paid[id][kind]:
            return false
        if stock[kind] < amount:
            return false
        stock[kind] -= amount
        paid[id][kind] += amount
        if staged and complete(id): build_order.append(id)
        return true

F8, the material side of serve:

    if world.counter.belt_serving:
        if not world.inventory.complete(Progress.FOOD_LINE) or journal.counter_stock < 1 or journal.served+1!=order: return false
        journal.counter_stock-=1
        journal.served+=1
        return commit_receipt("meal_served",world.counter.payment_rest.global_position)

Manual/worker serving likewise clears held_meal or worker_meal and increments served. F7's complete EMPTY settlement shape has no money/cash/credits field. F9 then instantiates MONEY for the exchange, clears presentations and emits served. This supports a visual payment observation; it does not support claiming a functioning wallet and spend loop. F11 adds transport custody and storage, not a cash balance. F12, settlement_status, constructs totals from journal.served and maps the cash display to totals.x. The current cash HUD therefore displays the served-meal counter; that is not proof of a conserved, spendable wallet.

F8, cancel_cooking:

    # A fallen carrier drops the in-flight presentation. Paid hopper stock and
    # machine work remain in the settlement ledger for the next simulation tick.
    works.cancel()

F1, zero-HP transition:

    if player_hp == 0:
        settlement_loop.cancel_cooking()
        _event("player_fall",actor.position)
        reset_time = 1.05
        character_kit.rest()

The reset branch subsequently assigns safe_start, restores MAX_HP, grants brief protection, resets encounters while preserving each living enemy's HP, and saves. Its existing numeric constants are recorded source facts, not proposed whole-game tuning.

## 4. Exhaustive bounded resource/currency inventory

“Exhaustive” here means every ID in the three identified source surfaces: the six-entry production registry; the inspected foundation's six raw and three processed IDs; and the 33 resource concept sheets. It is not a claim that an unregistered future resource does not exist elsewhere, nor an invented complete future recipe database. The JSON companion preserves every ID, category and mapping status.

### 4.1 Six production-registry entries

| Canonical registry ID | Current registry status | Existing source/destination commitment | Economic gap |
|---|---|---|---|
| wood | RESOLVED_BASELINE; production_ready true | Chop with axe; visible wood stack; storage/furnace/build. | Specific whole-game demand, remaining useful life and surplus behavior. |
| stone | RESOLVED_BASELINE; true | Mine with pickaxe; visible stone stack; storage/furnace/build. | Same; named destination alone does not prove a balanced sink. |
| metal | T09_FROZEN_ORE; true | Ore mining; processing/build storage. | Refining/product recipe and material purpose; survivor animation profile still T23_FREEZE_REQUIRED. |
| fuel | T09_FROZEN_SALVAGE; true | Dismantle with salvage pry tool; furnace/storage. | Explicit relation to coal/firewood and ongoing consumption; survivor profile unresolved. |
| fish | T16_FREEZE_REQUIRED; false | Fishing→food processing. | Tool, carry and human animation profiles, recipe and actual economic role not frozen. |
| wheat | T19_FREEZE_REQUIRED; false | Crop harvest→food processing. | Same; bread-like reference output does not establish flour intermediate or quantities. |

These are action contracts, not proof of a complete economy. Four production_ready flags do not imply whole-game runtime approval. [P2]

### 4.2 Current foundation resource use

| Foundation ID | Classification | Observed source/use in pinned foundation | Purpose status and proposed disposition |
|---|---|---|---|
| wood | Raw item | Gather/carry/store; pays camp offers and survivor plot; feeds saw→planks. | Immediate payoff exists. Preserve early construction; author later demand and reserve/surplus rules. |
| stone | Raw item | Mine/carry/store; pays offers; feeds quarry drill→blocks. | Immediate payoff exists. Freeze block-vs-raw use so processing has a useful reason. |
| meat | Raw item | Wolf/alpha-wolf drops; several material costs; cooker→meal. | Food/service path exists. Construction/axe-price meat is an authored current price, not inferred realism; review whether price teaches a coherent economy. |
| coal | Raw mineral | Collectible and storable raw ID. | No sink in reviewed offer/processor contracts. Keep collection from pretending to be valuable until distinct use or explicit merge/retirement is designed. |
| slate | Raw mineral | Collectible and storable raw ID. | No sink in those contracts. Give a particular architectural/region purpose or treat as a visual/source variant; do not create a duplicate grind. |
| metal | Raw ore | Inventory title is “Metal ore”; mined/stored. | No sink in those contracts. Register a useful machine/tool/construction chain before demanding it. |
| planks | Processed item | Wood output; production and storage receipt. | Actual product ID; downstream spend/sale not located in reviewed contracts. Bind to a meaningful construction/upgrade or finite goal. |
| blocks | Processed item | Stone output; production and storage receipt. | Actual product ID even though an older concept manifest excluded cut masonry as then unestablished. Current source takes precedence for this dated observation. |
| meal | Processed item | Cooked meat; carried, stored or conveyed to a real customer. | Real consumption/service purpose, but earned cash reinvestment still missing from inspected ledger. |

Transport keys stored_meal and meal_to_store are lanes/custody routes for the same meal, not extra recipe products or currencies. processed_wood, processed_stone, cooked and served are accounting counters, not additional inventory items. [F4–F11]

### 4.3 All 13 base render-sheet IDs

| Sheet ID | Category and evidence boundary | Mapping decision needed |
|---|---|---|
| wood | Raw-resource art | Corresponds to wood family; verify candidate geometry/presentation. |
| stone | Raw-resource art | Stone family. |
| slate | Raw-resource art | Foundation ID exists, but meaningful sink remains open. |
| steel | Refined-material concept | Do not equate with metal ore; freeze actual refining recipe and distinct use. |
| metal_ore | Ore concept | Foundation metal is titled Metal ore; record alias explicitly rather than invent another stock balance. |
| fuel | Salvage-fuel concept | Canonical fuel exists; relation to coal/firewood unresolved. |
| meat | Raw-food concept | Foundation meat exists; does not approve every wild species' food eligibility. |
| fish | Raw-food concept | Canonical but T16 unresolved. |
| wheat | Crop concept | Canonical but T19 unresolved. |
| cooked_food | Bread-like visual concept | Manifest explicitly denies canonical recipe claim; do not alias to meat meal automatically. |
| money | Physical earned-payment concept | Currency presentation; not a new material or premium-currency proof. |
| cargo | Container/load concept | Typed contents/custody wrapper; not a universal free-standing resource/currency by default. |
| coal | Supplementary reference concept | Manifest did not register gameplay content; later foundation does contain coal, but sink remains unproved. |

R1 has 13 concept sheets; user visual/production/native/runtime acceptance is not supplied by this sheet count.

### 4.4 All 20 expansion render-sheet IDs

| Sheet ID | Exact source status / boundary | Proposed economic treatment, not approval |
|---|---|---|
| deer_meat | proposed_species_cut | Source/appearance variant within meat unless distinct worthwhile use is frozen. |
| boar_meat | proposed_species_cut | Same. |
| rabbit_meat | proposed_species_cut | Same. |
| moose_meat | proposed_species_cut | Same. |
| squirrel_meat | proposed_species_cut | Same. |
| wild_bear_meat | optional_wildlife_cut_food_eligibility_unfrozen | Do not enable food drops merely because art exists. |
| wild_wolf_meat | optional_wildlife_cut_food_eligibility_unfrozen | Distinct from existing generic hostile-wolf meat source; no automatic species-cut migration. |
| wild_fox_meat | optional_wildlife_cut_food_eligibility_unfrozen | Same optional/unfrozen boundary. |
| lynx_meat | optional_wildlife_cut_food_eligibility_unfrozen | Same. |
| wolverine_meat | optional_wildlife_cut_food_eligibility_unfrozen | Same. |
| processed_meat_portion | reference_derived_visible_cooker_output | Choose an actual prep/product role or reuse visual state; not an obligatory intermediate. |
| cooked_game_meat | proposed_equipment_output_visual_state | Current foundation uses a named cooked_game_meat asset for meal; asset name does not create a second ledger product. |
| dried_meat | proposed_equipment_output_visual_state | Add only with distinct portable-food/service purpose; no automatic hunger/spoilage rule. |
| prepared_fish_fillet | proposed_fillet_form_not_implemented_recipe | Do not insert a fillet step without actual design and evidence. |
| cooked_fish | reference_derived_whole_cooked_fish_from_A016 | Preserve observed whole-fish processing silhouette; recipe quantities remain authored. |
| dried_fish | proposed_dried_state_from_visible_fish_drying_rack | Distinct useful purpose or visual variant; recipe unfrozen. |
| timber_planks | atlas_resource_and_proposed_equipment_mapping | Candidate mapping to actual planks needs explicit source/asset/canonical alias. |
| split_firewood | proposed_split_log_output_state_from_chopping_reference | Dedicated heat stock only if it creates a useful decision beyond raw wood/fuel. |
| hide | atlas_named_hide_with_proposed_folded_pickup_and_unfrozen_yields | Proposed gear/harness/insulation use; species yields and recipe not approved. |
| fur | atlas_named_fur_with_proposed_folded_pickup_and_unfrozen_yields | Proposed cold-weather/comfort gear use; distinguish from hide or aggregate. |

Companion animals are not prey inventory. A shared species name never authorizes hunting, processing or permanently losing a pet. The expansion manifest is 10 proposed wildlife cuts plus 10 processed/byproduct concepts, not 20 shipped economic IDs. [R2][R3]

### 4.5 Currency and noncurrency distinctions

| Name/concept | Current evidence | Needed purpose/contract |
|---|---|---|
| Earned cash / money | Reference videos show separate physical cash collection and spending. Foundation cash mesh exists; spendable wallet not shown in inspected settlement. [P7][F8][F9] | T17/T20/T33: one payout per fulfilled order, visible collection/custody, spendable balance, specific reinvestment uses and save/replay proof. |
| credits | Historical older-runtime customer-service term cited in R3 at f74a84a. | Treat as historical source vocabulary, not a second simultaneously approved foundation currency. Explicitly reconcile to earned cash or retire. |
| One primary premium currency | Policy slot required; exact final name and earning/spending schedule not established in reviewed sources. [P1] | T34/T35/T64: server-authoritative paid/granted units, clear optional uses, retained value, idempotent recovery. No invented gems/diamonds name. |
| Event currencies/tokens | No canonical event-currency ID established by reviewed sources. | Not counted as approved wallets. Prefer existing reward goods where sufficient; any new event wallet must justify purpose, exchange/expiry and recovery. |
| XP/experience | Not established as spendable currency by reviewed contracts. T12 progression uses completion facts/milestones. | Do not invent an XP wallet or cash exchange; if a future XP meter exists, identify it as progression unless explicitly spendable. |
| VIP | Permanent transparent entitlement in plan. | Not a currency, consumable wallet or difficulty signal. |
| Resource counters, purchase receipts, level/milestone facts | Progression/accounting state. | Never count as collectible currency solely because numbers appear in UI/save data. |
| Cargo/crates; storage/purchase pads | Physical custody/presentation or destination. | Container contents remain typed; art does not multiply economy IDs. |

The 29 resource-plot sheets represent storage, purchase and use states rather than 29 more resource/currency types. The older output coverage explicitly leaves flour, leather, canned meals, refined oil/fuel, steel plates, steel rods, charcoal, bricks, cut masonry blocks and workshop gears/nails unestablished in its historical scope. Some later foundation output (blocks) now has source evidence; this does not make the other proposals implemented. [R3][R4][F6]

## 5. Proposed stakes contract — for integration as design, not as already approved behavior

The player should be avoiding being overrun in the field, taking on a threat before preparing, leaving a useful expedition unfinished, interrupting production or missing an optional objective. A setback should create an understandable next action: retreat, regroup, repair, escort, recover, reprioritize or improve equipment. It should make capable survivors and pets useful.

| Situation | Proposed consequence | Player/crew counterplay and recovery | Design boundary |
|---|---|---|---|
| Overextending in hostile territory | Interrupted expedition; current safe-return behavior is the starting point. A uniquely owned recoverable cargo cache could add stakes if deliberately adopted. | Warning, retreat route, pet warning/defense, survivor escort/rescue; recovery route never depends on payment. | Cargo loss/recovery is a proposal, not observed current behavior; no arbitrary loss percentage or new player pack cap. |
| Ignoring a telegraphed attack on a working site | If raids are adopted, repairable equipment interruption or a local objective setback. | Guard priorities, repair jobs, targetable threats, protected essential recovery supplies. | Current camp sanctuary is not evidence of raids. No silent permanent building deletion or colony wipe. |
| Choosing the wrong production priorities | Slower project/service completion; materials remain accounted for and visible. | Clear demand, reservations, minimum stock policies, cancel/reassign, backpressure and alternate tasks. | Congestion, full outputs and wrong-item delivery are recoverable system states, not excuses to delete stock. |
| Entering a later environmental hazard without preparation | Explicit region-specific danger or temporary expedition limitation, only after that hazard is authored. | Readable safe route, equipment, companion specialty, extraction/recovery. | Desert, underwater, sky, volcanic, swamp and alien art does not establish thirst, drowning, oxygen timers, fall loss, poison or fuel drain. |
| Companion incapacitation, if adopted | Temporary withdrawal or recoverable rescue objective. | Team cover, healing/rescue role, safe fallback and clear return-to-duty state. | No automatic permanent death or loss of a purchased companion. Exact rules need explicit design. |
| Optional time-limited objective | Lose an optional bonus or retry the objective. | In-world warnings; ordinary progress remains viable. | No mandatory login streak punishment, deceptive countdown or payment-based rescue. |
| Repeated failure | Fairly bounded assistance/recovery in T13's behavior-only policy. | Lower overwhelming pressure, clearer route/help, competent companion intervention. | No purchase or VIP signals; no health-only escalation that erases counterplay. |
| App close, crash or save conflict | Preserve the last valid authoritative custody/transaction state. | Idempotent restore and free recovery from technical errors. | Offline erosion, duplicated losses or lost advertised purchase value are not acceptable design defaults. |

Proposed protected progress: completed land ownership, built upgrades, rescued companion ownership, banked stock and purchased value. If a system needs reversible damage, it must identify the damaged state, actual functional consequence, repair source and route back. Changing the whole-game protected-progress policy requires a concrete design decision; this audit does not pretend those protections were already fully frozen.

Do not solve absent stakes with routine resource confiscation. No arbitrary percentage of all materials, forced idle timer, compulsory fatigue/energy meter, pay-to-revive requirement, surprise offline damage or compounding unrecoverable debt is proposed. Whole-game tuning must come from authored encounters and measured normal-player routes.

## 6. Proposed resource-value contract

Every introduced collectible or currency needs an answer to **“What does this let me do that I want?”** A valid answer may be one meaningful finite use. Multiple sinks, infinite recurring demand, cash conversion and constant collecting are not mandatory.

For every canonical ID, record:

1. Identity: canonical ID, raw/processed/wallet/container/progression type, physical unit, aliases and variants.
2. Source: acquisition action, source region/stage, available quantity/regrowth or finite nature, actor permission.
3. Primary use: a named recipient, recipe, construction/upgrade, service order or optional goal.
4. Visible payoff: what changes in the world or in capability when spent.
5. Demand/progression: when needed, dependency chain, reachable source before demand, and whether use is one-time or repeatable.
6. Cost and yield: authored quantities, effort/travel/production time and actual ledger units; not numbers reverse-engineered from edited ads.
7. Surplus/retirement: keep for later, stop requesting, convert under an explicit fair rule, sell only to eligible demand, or make a finite goal stop emitting the resource. No hidden deletion.
8. Custody: pickup, carrying, storage, reservation, machine, transit, service, spend, recovery and save/reload accounting.
9. Presentation: specific material/shape, full action cycle, equipment state, readable transformation and feedback.
10. Proof: a real normal-play route with gain → usable stock → meaningful spend → visible benefit, including a zero-payment route where applicable.

### Purpose recommendations by family

| Family | Proposed primary value | Tradeoff / surplus decision |
|---|---|---|
| Wood / planks | Raw wood gives early shelter/building; finished planks serve selected later construction or upgrades. | Processing earns a distinct result; do not require planks for every trivial action. Protect already allocated project stock. |
| Stone / blocks / slate | Raw stone supports foundations; blocks serve selected durable structures. Slate needs a specific architecture/region role or a variant disposition. | Avoid three currencies that all buy the same thing at different exchange rates. |
| Metal ore / steel | Useful machine, tool or defense construction/upgrade through an explicitly authored refining chain. | Metal ore is not automatically ammunition; steel, rods and plates are not silently identical. |
| Salvage fuel / coal / split firewood | A clearly defined heat or machine-supply family if consumption is adopted. | Decide whether these are alternatives, different useful tiers, or aliases; three redundant fuel grinds are unnecessary. No paid energy wall. |
| Meat / fish / wheat / prepared foods | Service demand and visible food production are already central. Optional expedition/recovery food can be designed if useful and fair. | Species and presentation variants can share stock families. Bread-like output does not require an invented flour chain. |
| Dried food | A distinct portable supply/service role only if it improves a real decision. | No spoilage or compulsory hunger loop inferred from drying-rack art. Aggregate if mechanically identical. |
| Hide / fur | Candidate use in warm gear, harnesses or specific upgrades that visibly help people/pets. | Needs frozen yields/recipes and a distinct benefit. Do not lock basic survivor competence behind rare drops. |
| Earned money | Productive reinvestment in particular plots, equipment, services or optional personalization after real service. | Define what cash buys versus what materials build; no universal sell-all shortcut required. |
| Premium currency | Clear optional purchase value under existing fair-economy policy. | Baseline AI intelligence, core animations, recovery and realistic Level 1–100 completion must not depend on spending. |
| Cargo | Reliable grouping and transport of typed goods. | Container identity is not additional economic value unless a real reusable-container mechanic is deliberately authored. |

## 7. Task ownership and acceptance additions

These are proposed additions for authentic task owners, preserving their existing boundaries and dependencies. A later integration plan should update the actual task contracts/packets; prose alone is not an enforcement gate.

| Owner tasks | Needed contract / acceptance evidence |
|---|---|
| T07–T09 | Priority/context selection, unlimited logical player carry boundary, resource identities/units, full source actions; do not erase reserved resources or give all items generic motion. |
| T10–T12 | Material/cash plot requirements, meaningful upgrade payoff, survivor-enabled payment authority, progression before demand, one-time use and retirement. |
| T13 | Whole-game threat/recovery mapping; behavior-only adaptation; no hidden spend-based pressure or impossible recovery loops. |
| T14, T43 | Complete resource/wallet/cargo custody, interrupt/reload/cloud recovery and transaction idempotence. |
| T16–T20 | Authored fish/crop/food recipes; typed ports and reservations; physical service and exactly one real payment; downstream cash use. |
| T21–T22 | Damage/down/retreat/drop rules; combat and defense counters; if repair/refill/raid pressure exists, define and animate every actual state. |
| T23, T31 | Survivor all-task assistance including material/earned-cash plot contributions under delegated player priorities; broad carrying with truthful capacity; procurement reserves; failure recovery rather than stuck work. |
| T24–T30 | Species-specific support that materially helps safe travel, defense, gathering or rescue; no human-tool fallback or accidental prey identity. |
| T32 | Complete Level 1–10 gain→transform→service→payment→reinvest and setback→recover proof with final assets. |
| T33 | Canonical whole-game resource and wallet inventory; primary purpose, source, demand, progression, surplus/retirement; remove orphan collectibles; prove useful net payoff. |
| T34–T36 | Premium currency and permanent VIP separated from earned stock; fair optional benefits, purchase/restore/replay and retained value. |
| T37–T40 | Event prerequisites use approved resources; reward/expiry/recovery terms; no coercive surprise or invented new wallet without purpose. |
| T44–T52 | For each Level 11–100 region, register every resource and hazard/recovery route before integration; art alone does not establish mechanics. |
| T53 | Transport departure/arrival/interruption/recovery, exact cargo conservation and safe destinations. |
| T54–T55 | Hear/see warnings and consequences, accessible equivalents, distinct success/denial/recovery feedback. |
| T62–T64 | Whole-game replay and economy; measured $0 Level 1–100 route; explicit purchase value without compulsory paid relief. |
| T67, T70 | Regression and final source-bound gate; no unreviewed recipe, wallet, failure rule or animation state survives release. |

### Mandatory proof checklist proposed for the integration owner

- [ ] One canonical crosswalk reconciles foundation IDs, production registry IDs and every selected resource render; all art variants are classified.
- [ ] Every actual economy ID has the value-contract fields above; unknowns fail closed rather than shipping as busywork.
- [ ] A collected coal/slate/metal example reaches a worthwhile spend, or the item is explicitly removed/merged/deferred with save-safe handling.
- [ ] Planks/blocks have a payoff after processing; no stock ceiling leaves a mandatory route stuck.
- [ ] A real cash payout persists, cannot duplicate and buys an actual improvement.
- [ ] All-task survivor assistance includes eligible plot purchase/payment and significant mixed-resource carrying; player intent and resource reserves are respected.
- [ ] Current and proposed failure rules are separated; exact recovery/custody outcomes are documented before adding loss mechanics.
- [ ] Defeat, interrupted service, full storage, blocked belts, save failure and reload retain correct goods/paid progress.
- [ ] Every region's encounter and resource chain remains realistically completable at $0.
- [ ] Static, multi-angle, use-state, full-cycle motion and audio evidence match the actual candidate; no generic placeholder survives.
- [ ] Current acceptance policy applies: reference-sensitive dimensions at least 9.9; exact10 wherever stronger existing visual/style rules require it; all mandatory checks pass, zero unapproved deviations, independent review, missing evidence BLOCKED.
- [ ] T71–T80 remain undefined; no invented tasks or runtime-complete claims.

## 8. Review disposition

Source inventory and gap identification can be reviewed now. Runtime economy, fun, difficulty, animation and whole-game recovery are **NOT TESTED by this audit** and must not receive completion scores here. No evidence justifies saying every resource is already worth collecting or that pets/survivors already meet whole-game intelligence/parity expectations.

The next executable planning action is to integrate this inventory and the value/risk fields into the current task contracts, resolve canonical aliases and proposed failure rules, then implement and prove the resulting chains in each owning task. Maintain the latest reference policy; a numerical score is not a measured percent similarity and cannot average away an unproven sink, wrong resource animation or missing recovery state. [P6]

