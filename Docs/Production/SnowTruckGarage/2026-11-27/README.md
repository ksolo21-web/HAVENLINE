# Snow truck and fence-line garage — practical feature specification

## Scope and authority

Kaleb's current instruction defines the vehicle, its broad uses, its garage prerequisite, camp purchase, unlimited mixed cargo, HP, outside-camp cargo loss and automatic warehouse deposit. The [owner acceptance contract](OWNER_ACCEPTANCE.md) assigns these to VG01–VG09. The original request is preserved verbatim in [requirements](REQUIREMENTS.json) and [source evidence](evidence/source_recovery.json).

This package adds design, turnaround concepts and a reusable native custody component. It does not replace the active Codex game, commit another worktree's pending changes, edit operational workflows or mark historical tasks complete. The authentic plan still contains T01–T70. T71–T80 remain source gaps. Feature identifiers `VGxx` are overlay requirements, not new task numbers.

The selected game foundation is `trial/world-one-expansion-2026-11-26`, observed at `2f46e72e300a719f34ca9b0e9b718282a5a88ddd`; Build 13 reports implementation source `2654f5019b7212968d28600cb071bf1c231c9030`. The prior U3 rules work is a separate staged package, observed with freeze `29b11546165b8a32439a467c9b21cbd48f9c00b894734688468cac611bcb3f51` and publication pending. Its current rules inform this extension but are not silently imported or represented as published here.

The concurrent audit at `afc6d5da3a8605ba7baeb01b7bcc847c0a814347` records the same truck request and World 1 launch direction. World 1's possible 50 local levels remain a proposal; the global numbering and older 100-level launch scope need reconciliation. This feature therefore uses capabilities, routes and producers as prerequisites, without inventing an unlock level.

## Player experience

The garage is a substantial camp project. Its field-facing door occupies a chosen fence segment. The garage and parking bay sit inside the camp; the truck can leave and return through that broad opening while people retain their ordinary camp routes. Once the paid garage is complete and usable, a distinct purchase plot inside camp offers the truck with an exact, stable resource bill.

The truck is a useful optional investment in harvesting, combat and bulk hauling. It does not replace the baseline hand tools, worker jobs or companion roles needed to recover from a loss. The player can take a long mixed-resource trip without watching a cargo-capacity meter. The risk grows from leaving earned cargo aboard an exposed vehicle, not from an undisclosed inventory restriction.

Returning fully into the garage stops the blades and completes one warehouse transfer. A compact receipt shows the resources delivered. The unloading animation represents the transaction with a bounded number of bundles; it never spawns one physical object per stored unit or delays a large shipment in proportion to every unit.

## What is explicit, selected and still unmeasured

| Classification | Decisions |
|---|---|
| Explicit user requirements | Player driving; low horizontal blades for enemies, trees and mineable rocks; substantial relevant resource cost; completed garage before truck offer; truck purchase plot inside camp; garage door in fence line; all-resource unlimited cargo; HP; loss of remaining cargo when destroyed outside camp; garage-to-storage transfer; 360-degree truck and garage concepts. |
| Selected closure rules in this package | Full-footprint docking, safe camp travel with deliberate hostile-defense exceptions, blades stopped for docking/service/unload, whole-cargo-or-hold transfer, exact typed custody, serialized unload/destruction, inside-camp wreck salvage, separate player recovery, generation-bound replacement, maintained two pedestrian openings, no new fuel requirement. These are authored decisions, not claims extracted from footage. |
| Balance and presentation proposals | Exact bill quantities, HP, armor, movement speed, turning radius, hit rate/damage, mining efficiency, repair coefficients, garage dimensions and the relative point in World 1 when the capability gate opens. Actual assets, input, animation and device evidence are still required. |

## Purchase and progression

The garage offer requires an authorized camp-boundary placement and a constructive acquisition proof. Its bill uses existing material identifiers and currently obtainable production. `wood`, `stone`, `planks` and `blocks` are relevant candidates; a candidate is not mandatory merely because it is listed here. Slate or metal reinforcement may be included only where the authored catalogue and current World 1 supply path support it.

The truck offer remains unavailable until the correct garage generation is paid, complete, physically usable and linked to an existing storage house. Its separate in-camp plot uses a substantial bill selected from registered relevant materials. Existing `metal` means metal ore in the observed game; it must not be silently renamed to steel. `steel` may be used only after the catalogue contains a usable, obtainable steel producer and all its inputs. The words engine, wheel, blade and panel describe model parts; this package creates no inventory item called “parts,” “engine,” “tires” or similar.

Every proposed amount must be attainable through existing manual gathering and already usable or affordably obtainable producers. Prove the full quantity, prerequisite bills, recipe inputs and routes together. Do not finance a prerequisite with a future order payout or require the truck to acquire the materials needed to buy or replace itself. Recheck after a raid, destroyed producer or blocked route.

Once accepted, quote identity, bill, catalogue version, garage generation and target truck generation are frozen. Progression, reload, player wealth, VIP status or prior purchases do not reprice an accepted bill. Existing partial-contribution handling remains the owner of garage construction and any truck-plot contribution interface; the standalone vehicle purchase consumes a fully funded bill and does not implement that UI or escrow system. A stale garage generation pauses the attempt and exposes a recoverable owner-reviewed rebind/refund path without losing paid value.

“Substantial” is an economic intent, not a measured number. Balance owners must show collection and production time, opportunity cost versus other projects, utility gained and the ability to recover after repeated losses. No price or unlock-time claim is approved by this document.

## Garage and camp layout

The original fence and its collision remain in place throughout preview and construction. A single committed completion replaces the designated fence segment with the complete garage door/boundary state. A preview, payment alone or interrupted build cannot open a free breach. The geometry, navigation and paid-construction record change together.

The truck's complete body, low blade assembly, turning/reversing envelope and service access must fit. Garage dimensions are determined from the approved truck asset at existing character scale. Do not shrink Character 1, move the centered furnace or enlarge the opening camp simply to make a later vehicle fit. If the truck needs a later authorized camp expansion, that is a capability prerequisite; the Level 1 layout remains intact.

Two distinct usable bidirectional pedestrian openings remain available. The garage cannot silently count as a replacement for both or block them when its door is closed, a truck is parked or a queue forms. Workers, pets, customer approaches and driver exit points need real unobstructed paths. The garage connects to the inner camp circulation through its authored access; door and wall placement must match every selected view.

The closed garage door has a real collision and defense state. It cannot close through a truck, driver, worker or pet. An obstructed closing attempt stops or reverses with clear feedback; it must not crush or delete an actor. Enemy obstruction follows the actual combat/door rules and cannot create a permanently free closed-door attack exploit. Opening a door is not damage immunity.

The garage shell and fence-line door need explicit HP, generation and damage ownership in the camp lifecycle. A destroyed component loses its actual function and collision where breached. Paid repair follows material, tier and damage; boundary reconstruction retains its purchased boundary tier under the existing gate rules, while destroyed garage equipment follows level-1 repurchase. The actual model's dependency between shell, anchored door and bay readiness must be recorded before integration so two records cannot charge for the same reconstruction or leave a floating intact barrier.

Keep exterior terrain snowy. Interior pads and the approved camp floor may change; this feature does not authorize painted roads or paths outside camp.

## Driving, attacks and harvesting

Entering the truck switches the player's contextual controls and camera to a readable driving state. Provide deliberate steering, forward/reverse, brake and exit behavior suitable for landscape phones, tablets and foldables. A player may exit only into an actual reachable clearance position; if the nearby side is blocked, use another valid exit or show the blocked state without trapping the player permanently. Forced release after destruction uses the existing valid player recovery path.

The blades remain horizontal near the underside. They stop for docking, servicing and unloading, and safe ordinary camp travel defaults to stopped blades. A deliberate eligible-hostile defense action may operate inside camp when actual clearance and target rules permit; entering camp is not a blanket loss of the truck's attack capability. Incidental contact never damages friendly actors or owned structures. Wherever the blades operate, their contact volume must match the visible blade assembly and full motion. Do not reuse an unrelated orbiting axe placeholder as the truck attack. The terrain, intact fence, closed gate or rock geometry blocks contact where appropriate.

Tree and rock interactions use the existing typed resource profiles: normal depletion, authored yield, regeneration and the correct material output. Each source generation produces its depletion reward once, regardless of the number of blade colliders or overlapping frames. A mining node cannot award both the truck yield and a simultaneous player/worker yield. Unknown or currently ineligible nodes do not become free resources because the vehicle touched them.

Enemy damage requires a valid target, actual contact and the normal attack cadence. Truck attacks cannot hit friendly pets, survivors or customers as harvest targets. Enemy drops follow their existing eligibility and defeat receipt. Harvested or picked-up cargo belongs to one owner; cargo credited to the truck is not also credited to the driver's backpack or a worker. Ordinary mining/harvesting remains available after truck loss.

While occupied, the truck carries the player's actual presence into threat selection; entering a vehicle must not make the player disappear from defender/provocation logic. An empty parked truck is equipment, not a living defender. Existing U3 survivor hunting and per-enemy provocation remain intact. Pet and worker follow behavior must respect vehicle speed and route eligibility without teleporting cargo or creating compulsory autonomous driver jobs.

## Cargo and warehouse transfer

All ordinary portable resource families use one typed catalogue. This includes the game's existing raw and processed materials and any registered portable earned cash. XP, account unlocks and premium entitlements are not physical cargo and do not become truck loss targets. Adding later resource families requires catalogue/save migration; it must not introduce a hidden truck-type exclusion.

Cargo has no capacity, weight-derived quantity cap or stack-height limit. The native component represents counts as canonical decimal strings so large cargo is not rounded through floating-point serialization or limited to signed 64-bit inventory. Visual bundles, collision bodies and sound events remain bounded independently of amount. This is not a claim of infinite computer memory; valid large counts must never be silently truncated or converted into a paid capacity limit.

Successful docking requires the correct live truck generation, its bound camp and complete garage, the full hull and blade envelope inside the authored parking volume, and zero vehicle and blade motion. Merely touching the garage trigger, crossing the fence with the cab or stopping half outside is insufficient. The world adapter obtains positions and collision geometry from the actual scene; the UI cannot submit a trusted `inside=true` flag.

The garage has a built-in bulk-transfer relationship to one reachable storage house. No additional unrequested conveyor purchase is imposed as a prerequisite for the requested automatic deposit. Any visible movement or mechanical route must agree with the actual layout; a broken link, missing warehouse or destroyed destination produces an explicit hold.

On a valid return, transfer the entire typed cargo map to the warehouse in one committed operation. The warehouse ledger receiving a truck has no gameplay quantity limit and accepts every registered resource type. Its shelves and compartments are presentation, not capacity. Existing raw-category storage unlock checks cannot reject a resource the player already legitimately owns aboard this truck.

If the linked warehouse is missing, destroyed, blocked, stale, type-restricted or otherwise unable to receive the whole cargo, keep all cargo in the truck and show “Transfer waiting” with the concrete cause. Automatically retry after a new valid destination observation, using a new request identity after a changed hold condition. Do not drop goods, silently unload only the accepted families or charge a capacity upgrade. If a later design introduces finite usable shelf capacity, an explicitly warehouse-owned uncapped receiving ledger is required before this all-cargo guarantee can remain true; it cannot be invented as an unseen backup during runtime.

The concurrent audit's partial/full-destination suggestion is preserved as prior playtest advice. This package selects whole-cargo-or-hold behavior because the current warehouse has no approved finite inventory cap and the user's automatic full return should remain straightforward. Offline in this context means the destination is nonoperational; ordinary local single-player transfer remains usable without a network connection.

## HP, destruction and recovery

Damage applies once per validated contact to the current truck generation. HP, visual damage, animation and control state stay aligned. At zero HP, stop driving, harvesting and blades, cancel incompatible pending contacts and create a durable tombstone before replacement can occur.

The cargo-loss decision uses the complete truck footprint, including the authoritative blade envelope where it forms the operating footprint, against the saved camp boundary at the destructive event. A meaningful portion outside the boundary is treated as outside. Touching the gate with the front of the truck cannot shelter the whole load. Geometric tolerance is an implementation detail requiring world-unit verification; it is not a hidden gameplay grace zone. A damaged fence does not redefine camp ownership to follow the attacker or truck.

**Outside-camp destruction:** move every quantity still aboard into an auditable lost-value sink once. No salvage pile, recovery drop, resurrection, insurance grant or new truck copies that cargo. Previously completed warehouse transfers and the driver's separate personal inventory remain outside this loss operation.

**Fully inside-camp destruction:** the selected default is one persistent typed wreck-salvage owner. The truck is destroyed, its jobs stop and it must be replaced. The salvage is not free auto-banking or sanctuary immunity; the player must have a valid reachable claim. Claiming twice or reloading cannot duplicate it. Generic ruin salvage and outside-truck loss must never both run for the same vehicle generation.

This is a narrow explicit exception to the current GR13-style generic persistent equipment salvage rule: `vehicle destroyed outside camp → cargo lost`, while ordinary equipment, actor estates and an inside-camp truck wreck keep their appropriate existing custody rules. Do not broaden the exception to destroy the driver's backpack, warehouse stock or all camp assets.

Release the driver on destruction and restore valid input/camera. Use a reachable safe exit when valid; otherwise the existing player-down/recovery contract supplies a valid camp or initial safe arrival anchor and preserves the player's separate inventory. The standalone ledger does not perform this scene recovery and cannot approve it.

A surviving damaged truck can be repaired in its garage with relevant materials scaled to actual missing HP. No free full repair occurs merely by parking, entering/exiting, saving or changing the selected actor. Repair spending and HP restoration settle together and preserve already funded value across interruption. Exact rates require balance evidence.

A destroyed truck is bought again at level 1 through the valid garage plot, with a new generation and ordinary obtainable material bill. Purchased progression entitlements remain distinct from the destroyed live vehicle; rebuilding cannot regrant one-time unlock rewards or clone cargo. A destroyed garage must be rebuilt or a legitimate replacement garage assigned before repurchase. That recovery chain cannot require the missing truck.

No fuel meter, fuel consumption, refuelling wait, energy limit or premium replacement shortcut is introduced. If a later fuel proposal is made, its resource use, HUD, recovery and balance must be explicitly reviewed; the current request does not settle it.

## Persistence and race conditions

The driver, truck, warehouse, quotes, garage and camp lifecycle must share one authoritative world transaction boundary. Do not initialize duplicated copies of the same real inventory in both the standalone module and existing game ledgers. Decide the single owner and wire it through a conserved adapter before any live integration.

Each value-bearing action carries an immutable request ID, vehicle generation, relevant account/garage/warehouse generations and validated world observation. Repeating an identical committed request returns its existing receipt; reusing the ID for changed payload fails. A stale physical observation or changed destination before commit must not debit the truck.

Serialize unload and destruction in the same world event order. If destruction settles first outside camp, the remaining cargo is lost and the old truck cannot unload. If unloading settles first, those warehouse goods are no longer cargo and a later wreck cannot erase them. Bounded visual animations can finish or resume from the committed result; they do not own the quantities.

Snapshot/restore in the native component replays typed events, checks receipts, verifies a state digest and conservation, and replaces current state only after validation. The actual world-save authority must authorize the exact snapshot and prevent rollback to an older accepted world epoch. A digest is not a signed server receipt or an anti-cheat proof. Atomic disk/cloud persistence, old-save migration, whole-world consistency and crash injection remain integration gates. The component currently replays its full event history. Long continuous-sandbox use requires measured journal/checkpoint compaction that preserves idempotency receipts, tombstones and custody proofs; an ever-growing event list is not production scalability evidence. T14 and the performance owner must prove bounded resume time and retained replay protection before shipping.

The app's ordinary background/closed pause rule remains. No absent-player damage or invented offline transfer earnings are introduced.

## Visual, animation and sound acceptance

Concept sheets must show the truck and garage from front, rear, both sides and useful oblique/detail views. The blade plane must read as horizontal and low. Garage closed/open/interior or docked use states must establish the fence relationship, blade clearance and space for cargo transfer. Actual art selections and each critic observation belong to the art manifest; these are raster concepts, not a mathematically derived mesh turntable.

The later implemented vehicle needs complete start, idle, accelerate, steer, reverse, brake, stop, enter, exit, blade spin-up/run/stop, hit, miss, interrupt, tree/rock depletion, damage, wreck, repair, purchase and unload cycles. The garage needs full door open/close/blocked/reverse, construction, damage, breach and rebuild states. Review wheel contact, suspension and body weight, driver hands/feet/knees, blade collisions, door clearance, mixed cargo and interrupted transitions at the real gameplay camera and meaningful close-ups.

Listen to actual driving, reverse/brake, blade, typed impact, damage, warning, door, repair and transfer audio in quiet and busy scenes. Batch large unloading sounds. Provide readable non-color/muted equivalents, persisted preferences and reduced-motion handling. Screenshots alone cannot approve motion or sound.

Current reference-sensitive floors remain at least 9.9 per dimension, with stronger exact-10 material/visual gates preserved. All mandatory checks require evidence and a genuinely separate critic. No average score can compensate for a failed or missing dimension; user selection of the new design remains separate from technical review.

## Implementation boundary and next work

The new `tools/havenline/vehicle_rules` module covers bounded purchase/cargo/docking/damage/salvage/replay logic using a trusted world adapter. It does not supply vehicle physics, native assets, full acquisition proofs, garage construction, mobile controls, harvest/contact generation, repair animation, driver recovery or device certification. Its current API and named integration owners are in [INTEGRATION_MAP.md](INTEGRATION_MAP.md).

The [acceptance checklist](ACCEPTANCE.md) separates package/component evidence from the actual-game gates. [CHECKPOINT.json](CHECKPOINT.json) is a draft resumption record until root freezes the final artifacts, attaches independent results and verifies GitHub publication. It contains no fabricated test counts or runtime pass.
