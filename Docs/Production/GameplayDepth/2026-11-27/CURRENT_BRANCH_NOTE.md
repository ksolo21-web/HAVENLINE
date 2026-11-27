# Current branch note: Havenline source at 3fad812

**Observation only — no runtime execution, balance approval, animation approval or whole-game acceptance.** This separate note updates the latest-source context; the finalized Build 11 audit, inventory and consistency receipt remain unchanged.

The GitHub branch trial/world-one-expansion-2026-11-26 was observed at **3fad812b384335bd8ca9b5e47dc9d9557110eb4a** at **2026-11-27 11:39:25 UTC**. Its parent is 6435e5d4e58ec0d846dd89fbcf2efb8783e6af2e. Commit message: “Repair field collection, camp trading, crew and character locomotion.” Commit time: 2026-11-27T11:29:14Z. The new commit changes 80 files and is six commits ahead of the Build 11 source 989edd9283148e9f712387fb937ea36038cbd9d2.

Sources: [observed branch](https://github.com/ksolo21-web/HAVENLINE/tree/trial/world-one-expansion-2026-11-26), [exact commit](https://github.com/ksolo21-web/HAVENLINE/commit/3fad812b384335bd8ca9b5e47dc9d9557110eb4a), [single-commit change](https://github.com/ksolo21-web/HAVENLINE/compare/6435e5d4e58ec0d846dd89fbcf2efb8783e6af2e...3fad812b384335bd8ca9b5e47dc9d9557110eb4a). The mutable branch link does not replace the exact commit pin.

## Material updates that must accompany the historical audit

1. **Cash is no longer merely a mesh and served-count display at this head.** The settlement now stores pocket_cash and house_cash; inventory computes the uncollected till balance from earned served receipts; goods exchange moves actual balances between till, player and storehouse; the HUD displays pocket_cash. A meaningful cash-spending/reinvestment sink is still not present in the reviewed offers/exchange.
2. **Processed goods are now directly carryable and transferable.** The player can take planks, blocks and meals from outputs, carry them, store them and withdraw them. That is meaningful custody progress; it does not establish a downstream plank/block consumption sink.
3. **The old loose-drop cap deletion has been removed.** The 100-second played-time loose-drop expiry remains. Do not attribute the old oldest-drop-at-cap loss to this new head.
4. **Gradual camp healing now requires a fired hearth.** Safe-camp hit rejection and the zero-HP return/reset behavior remain. Do not say healing is unconditional merely because the player is inside camp.
5. **The owl has a separate meat-funded roost and ownership record.** Existing owners are migrated without new payment; this is not a new resource or currency.
6. **Survivor behavior has new service-priority and mixed-gathering source logic.** Shared worker plot payment is unchanged and still excludes the two conveyor offers. Full task parity, animation quality and whole-game usefulness remain unverified.

## Complete identifier census within the inspected current surfaces

| Category | Exact identifiers | Interpretation |
|---|---|---|
| Raw inventory, six | wood, stone, meat, coal, slate, metal | Same raw set as Build 11. metal is titled Metal ore. |
| Processor products, three | planks, blocks, meal | PRODUCT maps wood→planks, stone→blocks, meat→meal. |
| New goods exchange / pack keys, four | planks, blocks, meal, money | Three existing products plus one earned-cash transfer key; not four new materials. |
| Player product fields | hand_products.planks, hand_products.blocks, held_meal | Custody of existing products. held_meal already existed but now supports batches. |
| Cash custody | pocket_cash, house_cash, derived till_balance() | Locations of one earned cash family, not three currencies. |
| New reservation/custody map | withdrawn | Recently withdrawn stock protection, keyed by raw IDs, product IDs or money; not a collectible. |
| New owl plot ID | owl_roost | Separate construction/tender/ownership target; not an inventory item. |
| New owl ledger fields | owl_meat, owl_legacy | Cumulative meat payment and preserved entitlement flag; not new meat variants or wallets. |
| Transport lanes, eight | wood, stone, meat, planks, blocks, meal, stored_meal, meal_to_store | stored_meal and meal_to_store move the same meal. |
| Store product keys, three | planks, blocks, meal | Same product IDs; warehouse capacity/hand-stock rules changed. |
| Existing raw worker-load keys, six | wood, stone, meat, coal, slate, metal | WORKER_LIMIT remains expressed per kind in validation; no total-capacity-parity claim. |

The updated current census is therefore **six raw item IDs, three product IDs and one earned-money transfer key** across the inspected inventory/logistics/exchange surfaces. It does not add new premium or event currencies. The historical six-entry canonical production registry and 13+20 art-sheet classifications remain separate source surfaces and require reconciliation.

Evidence: [inventory](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_inventory.gd), [logistics](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_logistics.gd), [settlement](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_settlement.gd), [goods exchange](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_goods_exchange.gd), [goods pack](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_goods_pack.gd), [crew](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_crew.gd).

## Cash: source, custody and remaining sink gap

A fulfilled meal increments served. Inventory defines:

    till_balance = served - pocket_cash - house_cash

The exchange excludes a note still in its exchange animation when collecting from the till, then records collected cash in pocket_cash. Deposit moves player money to house_cash; withdrawal moves it back. The settlement validates nonnegative balances and prevents owned pocket plus house cash exceeding total earned served receipts. Legacy migration banks earlier served receipts into house_cash. The HUD now shows the player's pocket amount, and the physical pack/storehouse render cash from actual owned balances.

This is a source-level custody and conservation improvement. It is incorrect to apply the historical “cash display equals served count” observation to this head.

**The remaining reviewed gap is spending.** The 13 OFFERS still require only wood, stone and meat. The goods exchange collects, stores and withdraws cash; no spend target, price/debit function or reinvestment recipe was found in these inspected contracts. Thus there is now owned cash custody, but this bounded source inspection still does not prove the complete earn→spend→visible improvement loop.

Evidence: inventory::hand_goods / house_goods / till_balance; settlement::EMPTY / from_pre_register / valid; goods_exchange::_counter / _deposit / withdraw; [HUD::settlement_status](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_hud.gd); [progression::OFFERS](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_progression.gd).

## Resource sinks and transfers

The 13 existing material offers are unchanged. Survivor wood funding remains separate. A new separate owl roost consumes meat: field_crew defines OWL_MEAT = 6 bundles, and field_worksites receives the actual meat into owl_meat. Existing bundle size is ten raw units; this numerical cost is a current source fact, not a newly approved whole-game balance recommendation. owl_legacy preserves qualifying old ownership without repayment.

Planks and blocks now have hand custody and manual warehouse transfer. Machines reserve/deduct hand-held products from available output correctly in the reviewed rack formula. These transfers are not terminal consumption. No downstream plank/block spend or eligible customer sale was found in the reviewed contracts. Coal, slate and metal still have no use in the reviewed OFFERS or processor mapping.

The conclusion should therefore be “new custody and usability work is present, but every collectible's meaningful payoff is not yet proved,” not “none of the economy works.”

Evidence: logistics::rack; goods_exchange::_pickup_machine / _deposit / withdraw; [worksites::receive / demand](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_worksites.gd); crew::owns_owl / migrate / valid.

## Risk and recovery at this exact source

- _player_hit is unchanged from Build 11: it rejects hits inside camp and reduces HP outside under its guard conditions.
- Zero HP still cancels the in-flight work presentation, falls, returns to safe_start, restores MAX_HP and resets enemy encounters while retaining living enemies' current HP. The owl now advances during the return interval.
- No carried-material, product, cash, plot or companion debit was found in this inspected down/reset path. This is a bounded function-path observation, not a guarantee that every failure system in the whole game has been tested.
- cancel_cooking is unchanged: committed hopper stock and machine work remain in the ledger.
- is_camp_healing now additionally requires field_env.hearth_fire.fired; _advance_camp_heal calls restore_warmth. Being inside camp alone is insufficient for gradual healing under the current predicate.
- DROP_LIFETIME_SECONDS remains 100 played seconds. _step_drops removes expired loose goods. DROP_CAP and oldest-drop deletion in _place_drop were removed; lifecycle restore no longer rejects drop arrays by that cap.
- No new offline-confiscation, permanent companion death, cash fine or severe-loss policy was established by this source inspection.

Evidence: [opening::_player_hit / reset branch / is_camp_healing / _advance_camp_heal / _place_drop / _step_drops](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_opening.gd), [lifecycle](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_lifecycle.gd), [settlement loop::cancel_cooking](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_settlement_loop.gd).

## Carry and crew update

New goods_pack source assigns four fixed product/money bays below raw-material tiers and caps rendered representative pieces; logical quantities remain in the journal. The player can retrieve machine output before unattended outfeed reserves it, deposit batches and explicitly withdraw stock. That supports the existing unlimited-logical-inventory / bounded-visual-display direction.

The survivor adds an early customer-service opportunity before a field shift, checks whether customer meat is needed, alternates useful gather sites without returning after every pickup, and handles mixed cargo/unload timing. These are actual source changes, not proof of excellent AI under all congestion, priority and recovery scenarios.

worker_payment and _pay_from are unchanged from Build 11, including the restriction against Progress.LINES. The raw WORKER_LOAD remains six kinds. WORKER_LIMIT remains 500 raw units divided by ten-unit bundles, validated per kind with in-flight token/supply accounting. Do not convert that into an assumed total capacity or proof of all-task parity.

Character 2–4 assets, player wardrobe, crew/ballista and gait changes are present in the 80-file commit. This note does not inspect their full animations, visual quality, clipping or gameplay performance.

Evidence: goods_pack::BAYS / refresh; goods_exchange; [survivor::_leave_shelf / _continue_field_shift / _go_home_bulk / _unload_stream](https://github.com/ksolo21-web/HAVENLINE/blob/3fad812b384335bd8ca9b5e47dc9d9557110eb4a/HavenlineLevel1/field_survivor.gd); inventory::worker_payment / _pay_from; settlement::valid.

## Verification boundary

Verified for this note: branch/commit metadata; the exact single-commit changed-file list; direct reads of the named current source files; selected comparisons with the previously read Build 11 functions; raw/product/goods identifier census; source file Git blob identities and SHA-256 hashes recorded in CURRENT_BRANCH_NOTE.json.

Not executed or approved here: Godot tests, Android build, gameplay replay, save-migration runtime tests, economy tuning, complete late-game progression, actual animation cycles, companion intelligence, audio or ≥9.9/exact10 visual acceptance. Test files added by this commit are observed files, not test runs performed by this audit.

The GitHub Build 11→head comparison returned 300 file records and may be capped. It was used for commit ancestry only; this note does not claim its returned file list covers that entire multi-commit span. The 80-file immediate-parent comparison and pinned direct source reads support the bounded findings above. No remote branch, candidate, runtime asset or finalized historical audit was modified.

