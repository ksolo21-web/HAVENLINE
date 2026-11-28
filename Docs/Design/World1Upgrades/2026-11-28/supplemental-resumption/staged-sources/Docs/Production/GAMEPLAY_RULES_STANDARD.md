# Havenline — current gameplay rules

## Authority and scope

These are the current forward rules after the user's three messages recorded verbatim in [USER_RULES.json](GameplayRules/2026-11-27/USER_RULES.json). **U3 is the latest correction:** survivors can hunt and initiate authorized attacks. Enemies may retaliate against the survivor that provokes them. While the player or a valid defending pet is nearby, player/pet/camp objectives are eligible direct targets; unprovoked survivors are not, even as a fallback. When both player and defending pets are too far away, all characters and destructible camp equipment become eligible targets.

The [machine-readable contract](GAMEPLAY_RULES_CONTRACT.json) contains GR01–GR20. It supersedes earlier free companion revival, free structure repair, permanent sanctuary and fixed one-meal staffing assumptions. The intermediate survivor self-defense-only restriction is withdrawn. [SUPERSESSION.json](GameplayRules/2026-11-27/SUPERSESSION.json) records each replacement; historical packages retain their original bytes and meaning.

These rules retain all seven attacking pets, unlimited logical mixed carrying, simple contextual controls, the reference renders, the existing task graph and a realistically achievable free-player route. Reusable native rule components are provided under tools/havenline/gameplay_rules. They are **not imported into the current Codex field build**. Headless logic evidence and actual scene/motion/audio/device evidence are separate.

## 1. The counter is stocked in bulk; customers serve themselves

Only the player and actually unlocked living survivors perform stocking and money logistics. Delivering stock, owning a conveyor or having a queue never creates a cashier or extra serving survivor.

The counter has a distinct physical stack area for each requested processed product and a separate cash stack area. A customer can request a combination of eligible processed goods; the catalogue is not limited to meat or food. Raw meat and cooked meat retain different item identities. Planks, blocks, steel and future processed outputs can become saleable when their authored product/customer handling is ready. Existing art variants do not automatically create new inventory IDs.

An authorized worker can load a useful bulk quantity of several products, travel with the same logical mixed carrying policy as the player, unload the requested stock, collect all available ordinary cash and deposit it at a valid destination. A job stops at its useful demand target. An unlimited inventory does not mean endless harvesting.

Customer service follows one clear sequence:

1. Generate a reachable, progression-appropriate quoted basket.
2. Reserve its complete quantities from typed counter stock.
3. Animate the actual customer's pickup and money placement.
4. Commit the basket transfer and exact cash creation together, once.
5. Let the customer leave; cash remains available on the separate counter pile.
6. Let the player or an unlocked worker bulk collect and carry that cash to storage or a permitted purchase.

Stocking is not a sale. A decorative pickup is not payment. No success cue or income occurs for an unpaid, cancelled or replayed order. Logical bulk transfers may use aggregated visible stacks and a short physical flow; mesh count must never change value.

If a customer flees or dies before settlement, release its basket back to counter stock or the counter's persistent ruin salvage. If settlement already committed, preserve the cash and customer ownership. Purchased customer goods do not become player resale loot on that customer's death.

If the counter, storehouse or conveyor is destroyed, route its remaining player-owned contents into exactly one typed salvage owner. Workers retain cargo or choose a real alternate destination; they cannot deposit into a destroyed building or invent an invisible wallet. Existing paid stock and cash are not silently deleted.

### What the current source actually does

The inspected Build13 source has working player bulk meal/cash groundwork, but counter stock remains a meal-only count, worker serving carries one meal, and stock/conveyor state can create a CounterAttendant. The function named show_register draws cash notes; that name does not prove a physical register exists. Preserve useful money presentation while replacing the staffing and custody behavior. [Exact source findings](GameplayRules/2026-11-27/SOURCE_AUDIT.json).

## 2. Demand and construction costs grow with progression

Customer baskets, plot bills and upgrades use progression band, unlocked opportunities, target type/tier and an authored catalogue. Both the resource types and quantities may change. Challenge cannot use payment history, VIP or current wealth as a hidden penalty.

A product is eligible when there is a **constructive acquisition path for the required quantity**. This may use an operating owned producer or a plot the player can actually buy and operate now. The proof includes:

- Account/region unlock and a reachable route.
- Renewable or sufficient remaining raw inputs.
- Available tools and actor capability.
- Every prerequisite plot, recipe, machine and required input quantity.
- The actual purchase/rebuild/upgrade bill along the path.
- Current machine HP, blackout state, capacity and transport access.
- Available ordinary money where genuinely required, without using this order's unearned payout.

A machine cannot require its own only output to buy itself. An upgrade cannot depend solely on a descendant it unlocks. A customer cannot be the only money source needed to buy the machine required for that same order. A destroyed-owned flag is not operating production.

For example, a cooked-fish order can be valid before buying its producer if fishing access, the processor plot, its attainable bill and all necessary inputs are available. It must be rejected if the processor requires an unavailable region material or its own unproduced output.

### Stable quotes and damaged production

Persist quote ID, target generation, catalogue version, progression snapshot, items, quantities, reward and committed contributions. Ordinary level advancement does not reprice an accepted or part-paid quote. Cancelling/reloading does not roll a new bargain.

Destruction or route loss requires rechecking acquisition. If a recovery path still exists, explain it. Otherwise pause or cancel unsettled work and conserve its goods/contributions. Do not demand impossible output or confiscate partial progress. New quotes can use the newer progression band; existing valid accepted quotes keep their agreed terms.

If a frozen unpaid customer order becomes genuinely unobtainable and other useful orders remain possible, it must not lock the counter forever. Retire it once using the trusted current-world revision and actual owned/reserved custody, with no cash payout and no loss of uncommitted goods. A complete reserved basket, a settled sale or any still-feasible acquisition path prevents this retirement. Preserve the retired quote identity and advance the offer ordinal; a stale quote cannot reserve again after reload. Ordinary cancellation of a feasible order retains its frozen terms and cannot reroll demand.

A bounded active-order set prevents mass reservation of every future offer at an early price. Exact mix, amount, payout and throughput require real free-player measurements; the executable catalogue is a starting fixture, not a claim that all100 producers are implemented.

## 3. Survivors hunt and can provoke retaliation

Latest U3 permits assigned hunting and authorized attacks. A survivor that initiates an attack against an enemy becomes a valid retaliation target for that enemy. A legitimate attack attempt can provoke retaliation even when the strike misses.

Huntability is an explicit target role. A friendly pet and a hostile or huntable animal sharing a visual species are still different identities. Owned pets, rescued friendlies and customers cannot be selected as prey.

Keep ordinary work useful under pressure: gather, hunt, haul, restock, collect cash, buy authorized plots, construct, repair and support defense. Jobs retain player goals and budget limits. Attack, retreat, recall and resume must conserve cargo and release stale reservations.

## 4. Enemy priorities protect neither invulnerability nor mindless targeting

| Situation | Required targeting behavior |
|---|---|
| Player near; defending pets far | Target valid player/pet/camp objectives; an unprovoked survivor is not a direct target. |
| Player far; a living eligible pet actually defending nearby | Defender-aware priority remains; the player being far alone does not trigger unrestricted targeting. |
| Survivor attacks an enemy | That enemy may retaliate against that survivor, even with defenders nearby. |
| Player and all eligible defending pets are far | The encounter may target all characters and destructible camp equipment. |
| Player/pets stand inside intact defenses | Attack reachable defenders, the blocking boundary or a valid camp objective; camp coordinates do not make the interior permanently immune. |
| A pet exists only as an undeployed roster entry, is dead or is not defending | It does not count as a nearby defender. |
| Target is blocked or unreachable | Choose a credible reachable approach, blocking structure or alternate objective; do not hit through geometry. |

An unprovoked survivor remains ineligible for direct targeting while a valid defender is near even if all preferred targets are absent or unreachable; enemies seek a valid approach or attack a blocking defense. Target eligibility is not collateral-damage immunity. An actual valid strike can hurt a survivor in its contact area. The latest rule replaces the earlier inside-camp/outside-survivor exception: crossing the camp boundary alone does not automatically make an unprovoked worker the first target.

Warn the player before the defense boundary is crossed. Use distinct enter/exit thresholds and stable target commitments so small movements do not cause repeated target flipping. Presence is scoped to the actual camp/encounter.

Distance-based rendering and region unloading must preserve logical enemies, HP, provocation and siege state. Walking away cannot despawn a threat or refill its health. Active offscreen encounters use the same conserved outcomes; app background/close pauses ordinary simulation and causes no absence raid.

For scheduled camp raids, the selected starting rule is one admitted siege per solo world, tied to a saved named camp and warning through the final committed strikes and retreat. Travel does not cancel or move it to another camp, and a camp in blackout receives no new scheduled raid. Actual roaming threats remain able to attack under U3. The cross-camp scheduler is a required world-integration task, not a feature claimed by the standalone per-camp test component.

Visitors evacuate when threatened. They are not secretly invulnerable when caught in an unrestricted siege. Settled sales and unsettled reservations follow the counter rules above.


### Scheduled raid warning and opening cadence

The later README-only commits [444dad5](https://github.com/ksolo21-web/HAVENLINE/commit/444dad5cb2bfcde042ff19c5e322d44498e3ddc0) and [ee3ef9e](https://github.com/ksolo21-web/HAVENLINE/commit/ee3ef9e38923a02c29512cc0652440c14ca3672b) preserve the prior audit documents and add a fixed owner requirement: a full **five-minute active-play warning** before scheduled-raid damage. Name the threatened camp, show5:00 from wherever the player explores, provide sound and equivalent muted cues, and save/restore remaining time. If due admission is ineligible, wait until eligible and then give the full warning. Prepared defenses must be beatable with ordinary stage-available equipment; failure must retain a real retreat and raw rebuild path.

The opening frequency remains a **playtest proposal**: first warning/attack at20/25 active minutes after basic defenses become available; following a win, warning at40–55 and attack at45–60 minutes after encounter end; following failure, warning no sooner than55 and attack no sooner than60 minutes. Select the repeat interval once, persist it and the authoritative outcome/end time, pause out of active play, and allow one pending/active scheduled raid. Regional cadence still requires measurement. Tune strength/composition/patterns before shortening intervals.

The current standalone lifecycle has no countdown or interval scheduler. Its internal warning_given flag must mean the trusted world adapter has completed the full warning; it must not mean the warning was merely displayed. complete_retreat does not classify a defended win versus core loss; the world encounter director must supply that outcome. These are explicit integration gates, not new native behavior or game approval. Exact source bytes and blob identity are in Review/ConcurrentAudit/LateRaidWarning/.

## 5. Death costs a replacement purchase

Pets and survivors have real health and can die. At zeroHP, tombstone that live instance, stop its attacks and jobs, release transient claims and transfer its cargo into one persistent typed estate cache. A corpse cannot continue working or count as a defender.

Reacquiring the unlocked survivor/species requires an ordinary earnable-resource/cash purchase. Commit one new live instance, with an identity/generation distinct from the dead one. There is no automatic respawn or free care revival.

The user explicitly required equipment to restart at level1 but did not require companion level loss. The selected replacement rule therefore preserves earned companion level/XP/skills, account unlocks and permanent paid entitlements. The replacement does not receive a cloned copy of estate cargo. Claim that cache separately, once.

First acquisition and replacement use different receipt identities. Loading an old save, replaying payment or switching the deployed team must not resurrect a tombstoned instance or bypass its replacement bill. No mandatory repeat real-money payment is introduced.

The player's down/return policy remains separate: preserve owned inventory and progression, restore working controls and choose a valid recovery anchor. A destroyed camp under attack cannot be assumed a safe return point.

## 6. Fences, gates and equipment can be destroyed

Fences and gates have high finite HP. Each placed equipment class has authored HP, damaged presentation and a destroyed state. Boundary destruction must open the corresponding collision/path route; no invisible fence remains.

| Object state | Required recovery |
|---|---|
| Damaged fence/gate | Fund its repair plot using material appropriate to purchased tier and missing HP. |
| Destroyed fence/gate | Reconstruct through its repair plot at the purchased tier, with a larger damage-based bill. |
| Damaged machine/equipment | Fund a repair quote appropriate to its material, tier and missing HP. |
| Destroyed machine/equipment | Rebuy a new level1 generation; earn its upgrades again. |
| Destroyed furnace | Enter local camp blackout, then rebuild level1 using the reachable emergency bill. |

A repair quote buys a bounded amount of actual restored HP. New incoming damage does not enlarge that already paid budget. Committed repair effort that is subsequently damaged was real work; cancellation cannot refund consumed effort and keep the healed HP. Uncommitted escrow returns if the target generation is destroyed or replaced.

Every content-bearing object—counter, storehouse, processor or conveyor—needs a typed content disposition at destruction. Damaged/ruined presentation, collisions, operating state and save state must agree.

## 7. Furnace destruction causes a camp blackout

This is the selected design response to the requested hefty penalty:

- Stop automated production in the affected camp.
- Stop admitting new customers there.
- Pause ordinary worker jobs that rely on normal camp operations.
- Preserve settled value, remaining stock and recoverable contents.
- Rebuild the furnace at level1, then repurchase its higher upgrades.
- Pay a substantial raw-material bill that grows with progression and the lost furnace tier.

Manual gathering, recovery-oriented worker jobs, hunting for recovery supplies, salvage/cash collection, combat, repair/rebuild funding and ordinary companion replacement remain available. Existing safe travel/recovery routes remain usable. Other camps are not automatically shut down.

**Starting calibration:**400wood +200stone at region band0/lost tier1. The sample scale is (10000 +1500×region_band +1000×(lost_tier−1))/10000, rounded upward for each material. These numbers are executable tuning fixtures, not measured final balance.

The permanent baseline player gathering capability survives placed-equipment destruction. Each region must provide a reachable renewable manual wood/stone recovery path. The emergency bill cannot require cash, a helper, processed goods or a producer disabled by that same blackout.

A siege has a finite saved objective/attack budget. When core destruction achieves that encounter's defeat objective, attackers finish already committed strikes and retreat without a victory/clear reward. Scheduled new camp raids pause through reconstruction. Roaming threats remain possible. This creates recovery room without an immortal camp, endless waves or a reward for deliberately losing.

## 8. Full presentation and integration are mandatory

Every affected actor/tool/machine needs its applicable full use states: approach, anticipation, contact, commitment, success, miss, blocked/full/empty, interrupted work, damage, death/ruin, replacement, repair and restoration. Counter buyers need grips and carried presentation appropriate to the actual product, including non-food processed goods.

Sound must distinguish attack tells, hits, boundary breaches, lowHP, death, pickup/payment, repair and furnace failure/restoration. Review actual listening under simultaneous play. Critical meaning remains readable muted, without color alone and with reduced motion.

Migrate Build13 saves without retroactive deaths or lost paid value. Remove only the obsolete attendant role, preserving customer assets and real unlocked workers. Add explicit spent-cash accounting before spending so old derived cash cannot reappear after purchase.

The standalone native components test rule decisions and conserved transactions. Existing owners still must connect them to the actual field scene, actors, contact events, pathing, snapshots, presentation and source-bound test harnesses. They do not confer a new game score or task approval.

Final reference-sensitive dimensions remain at least9.9 individually, with stronger exact10 visual/material gates. Actual full cycles, meaningful views, listening, free-player progression and physical-device evidence remain mandatory.

## Read the implementation handoff

- [Current task rule map](GameplayRules/2026-11-27/TASK_GAMEPLAY_RULES_T01_T80.md)
- [Revised complete game decisions](WHOLE_GAME_COMPLETENESS.json)
- [Revised100 outcomes and economy](GameplayRules/2026-11-27/PROGRESSION_ECONOMY_GAPS.md)
- [Actor/combat contract](GameplayRules/2026-11-27/ACTORS_COMBAT_GAPS.md)
- [Twelve transaction boundaries](GameplayRules/2026-11-27/TRANSACTIONS_AND_RECOVERY.json)
- [Current source audit](GameplayRules/2026-11-27/SOURCE_AUDIT.json)
- [Native logic and integration evidence](GameplayRules/2026-11-27/README.md)

T01–T70 identities, dependencies, ownership and historical status remain preserved. T71–T80 definitions and complete original-video custody remain explicit source gaps. Authored Level71–80 content is distinct from those missing task IDs.

Scheduled encounter identity must persist onto attacker/damage records. Relabelling a scheduled attacker as a roamer cannot bypass the warning; actual independent roaming threats retain their normal rules.
