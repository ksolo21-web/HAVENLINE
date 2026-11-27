# Vehicle rules — integration and remaining gameplay work

## Current component boundary

The standalone project is `tools/havenline/vehicle_rules/project.godot`. It is isolated from `HavenlineLevel1/field_opening.tscn`; no driving build is produced by this packet. Actual input, scene geometry, contact generation, construction, obtainable-price proofs, driver recovery and complete-world persistence remain integration work.

Run from repository root:

```sh
godot --headless --path tools/havenline/vehicle_rules --script res://tests/run_all.gd
```

The source-bound result and input identities belong to `tools/havenline/vehicle_rules/evidence/` and the root's final candidate freeze. Builder results and independent review have different provenance. This document records interfaces, not an approval score or stale test total.

| Current API | What it supplies | What the game adapter must prove |
|---|---|---|
| `initialize(adapter)` | One bound authority, registered resources, initial accounts and conserved genesis. | These are actual owned balances, imported once; no duplicate game/module owner. |
| `admit_quote`, `purchase` | Stable quote identity, relevant generations, garage-ready predicate, whole-bill debit and level-1 truck creation. | Actual in-camp plot, paid completed garage, one bay, obtainable full bill and legitimate source catalogue. Existing partial-contribution escrow stays with the economy owner. |
| `rebind_quote_garage` | Preserve an unpaid frozen quote across a valid garage replacement. | Authentic paid rebuild and correct garage/camp generation; no free rebuild or price reroll. |
| `rebind_quote_payer` | Preserve the frozen unpaid bill when an old payer generation is unusable. | Legitimate authorized payer transition and no cloned balance/partial contribution. |
| `load_cargo` | Exact decimal typed movement from one eligible account into a live truck. | Real contact, reachable source, owned resource quantities and once-only harvesting/drop creation. It does not mine a rock or spawn a tree yield. |
| `park_and_unload` | Full supplied hull/blade envelope inside bay, stopped vehicle/blades, current garage and all-resource receiver, whole-cargo move or hold. | Correct native geometry and scene transforms, actual warehouse route/readiness, automatic retry trigger, truthful visible transfer. |
| `apply_contact_damage` | Contact uniqueness, current HP/generation, footprint-based outside loss or inside salvage, durable tombstone. | Real eligible attack/contact, authoritative complete camp/vehicle polygons, player release, wreck presentation and stopped controls. |
| `storage_destroyed`, `reopen_storage` | Conserved warehouse estate and empty next-generation reopening. | Actual camp-lifecycle destruction and paid rebuild receipts; no second estate in a parallel inventory system. |
| `claim_inside_salvage` | Once-only typed claim into a valid actor account. | Actual accessible cache, live claimant and contact; not direct banking into a destroyed warehouse. |
| `snapshot`, `restore`, `state`, `audit` | Typed event replay, receipt/digest/conservation checking and defensive state copies. | Exact full-world save authorization, no rollback to stale accepted world epochs, atomic disk/cloud persistence and actual prior-save migration. |

The adapter methods are `vehicle_authority_id`, `capture_vehicle_bootstrap`, `validate_vehicle_bootstrap`, `capture_vehicle_observation`, `validate_vehicle_observation`, and `authorize_vehicle_restore`. Physical facts come from this bound adapter and are revalidated before commitment; they are not trusted player-supplied booleans. The test adapter is a fixture, not a shipping source of truth or a security service.

The vehicle component uses full event replay. Before long-session shipping, T14 and the performance owner must implement and measure journal/checkpoint compaction with retained request receipts, destruction tombstones and custody proofs. Never discard replay protection to shorten the log. Measure save size, resume time and interrupted compaction across an extended sandbox session. No unlimited event-history scalability claim is made here.

## Dependency-aware next actions

| Stage | Named coordinating owner | Concrete next action and exit evidence |
|---|---|---|
| Component packet | `/root/vehicle_gameplay` | Supply exact final module/test inputs and actual native result; respond to independent defects. |
| Concept and documentation packet | Alfred (`/root`) with `/root/recover_plan` | Freeze selected art, requirements, task overlay and source evidence; preserve concept selection versus production approval. |
| Independent review | Separate critic coordinated by Alfred | Inspect actual frozen outputs, rerun meaningful adversarial cases and keep rejected evidence; missing game evidence stays blocked. |
| Isolated publication | Alfred (`/root`) | Recheck live refs, publish the isolated addition and verify exact commit/tree/file readback. Do not absorb pending U3 work or alter the game branch. |
| World adapter and scene integration | Alfred resolves the actual Codex field owner first | Bind one inventory authority and current field source, then implement actual plots/garage, vehicle/controller/contact, loss/driver recovery and world saving under legitimate paths. |
| Play and shipping review | Existing task owners coordinated by Alfred | Prove scene loop, 2-exit circulation, normal camera, full cycles/listening, old saves, balance and physical-device performance. |

These are coordination actions, not new claims over another task's protected paths. The [task overlay](TASK_OVERLAY.json) preserves existing IDs, dependencies, states and historical frozen scopes.

## Wider gameplay gaps that remain in the continuation

The following recovered seams are retained so a truck addition does not displace the existing gameplay-gap objective. The U3 source audit supplies the earlier exact bindings in [source recovery](evidence/source_recovery.json); these are not claims of a new full-game playtest.

| Existing gap | Actual field seam | Next implementing responsibility | Evidence needed |
|---|---|---|---|
| Self-service mixed baskets and no spawned attendant | `field_counter.gd`, `field_settlement_loop.gd` | T10/T12 early contract and T17 service owner: real customer reserves, picks up and pays once; remove attendant role. | Mixed basket, flee/death/reload and separate visible cash. |
| Unlocked survivors bulk-stock, collect cash and purchase ordinary plots | `field_survivor.gd`, `field_goods_exchange.gd`, `field_inventory.gd` | T08/T23/T31: shared mixed typed custody and authorized budgets, including conveyors. | Full bulk routes, interruption/death, concurrent jobs and exact payment. |
| Obtainable dynamic orders/plot costs | `field_progression.gd`, `field_worksites.gd`, `field_settlement.gd` | T10/T12/T13/T33: bind actual sources, quantities, recipes, prerequisites and immutable quotes. | No circular producer bill, unavailable resource or future-payout funding; accepted terms survive change. |
| Threats continue while player explores | `field_encounters.gd`, `field_enemy.gd`, `field_opening.gd` | T13/T21/T31: U3 defender/provocation rules, saved camp identity and full 300-second active-play raid warning. | Real contact, offscreen continuity, no distance deletion/immunity or warning bypass. |
| Survivors hunt; all seven pets attack and remain useful | Survivor, owl and other species controllers | T21/T23/T24–T31: actual living actors, credible hunts/attack/specialty/escort behavior and paid casualty replacement. | Full species cycles, defeat/cargo estates and useful eligible work. |
| Fences, gates, machines and camp equipment are destructible | Environment, navigation, processor, storage, counter and logistics instances | T21/T22 plus equipment owner: exact HP, breach, paid repair and level-1 equipment replacement. | No phantom collision, repeated repair credit or duplicate ruin contents. |
| Furnace blackout and zero-state recovery | Hearth, opening loop, processors and objectives | Camp/economy owner: pause local automation, preserve custody and fund raw-only recovery manually. | All producers/companions lost; reachable free-player rebuild path and finite siege retreat. |
| Shared custody and whole-world saves | `field_save.gd`, `field_lifecycle.gd`, inventory and settlement | T08/T14: single transaction boundary and migration; vehicle reducer is one participant. | Real old saves, crash injection, mixed-era rejection, long-session compaction and no cloned balances. |
| Conveyor routes and hardware match selected designs | `field_conveyors.gd` and route/native assets | Conveyor source owner with T31: one destination admission authority and actual player-chosen routes. | Full/incompatible holds, correct fittings/proportions and busy-loop mixed delivery. |
| Meaningful material sinks and launch progression | Actual producers, prices, T12/T32/T33 | Reconcile World1 continuous sandbox and capability milestones with the older 100-outcome contract. | Distinct useful progression, measured pricing/recovery, no invented final 50-level count. |
| Full visual, animation, audio, input and device evidence | Native assets/actions, HUD, camera and audio | Existing relevant C1–C11 specialists and feature owners | Actual scene comparisons, complete playback/listening and physical device/load tests; static concepts cannot close them. |

The first practical game step is the single-custody/world-adapter binding; it is a prerequisite to safely combining bulk service, truck unloading, repairs and loss. Independent component preparation can continue before that binding, but live integration cannot borrow a standalone pass as proof of those shared transactions.
