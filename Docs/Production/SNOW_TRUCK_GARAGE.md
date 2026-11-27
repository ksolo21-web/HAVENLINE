# Havenline — player snow truck and fence-line garage

The player earns a garage inside the camp, then buys a snow truck on a separate camp plot. Low horizontal blades let the truck attack eligible enemies, fell trees and break mineable rock. Its mixed cargo has no gameplay capacity limit. A complete return to the garage banks all cargo in the storage house. Destruction outside the camp loses everything still aboard.

This is an additive feature package on `feature/snow-truck-garage-2026-11-27`, based on published plan commit `a4e643aeb563b6f9cfda8b840c0651d13326eec8`. It preserves the original 70 task definitions, historical approvals and active Codex foundation. T71–T80 remain missing-source questions. The current standalone rules and generated concepts do not constitute a driveable game build.

## Read the feature

- [Practical design and selected gap decisions](SnowTruckGarage/2026-11-27/README.md)
- [Machine-readable requirements and acceptance scenarios](SnowTruckGarage/2026-11-27/REQUIREMENTS.json)
- [Acceptance checklist and evidence boundaries](SnowTruckGarage/2026-11-27/ACCEPTANCE.md)
- [Existing task responsibilities and dependencies](SnowTruckGarage/2026-11-27/TASK_OVERLAY.json)
- [Native component and actual-game integration map](SnowTruckGarage/2026-11-27/INTEGRATION_MAP.md)
- [Source bindings](SnowTruckGarage/2026-11-27/SOURCE_BINDINGS.json), [source recovery](SnowTruckGarage/2026-11-27/evidence/source_recovery.md), and [resumption checkpoint](SnowTruckGarage/2026-11-27/CHECKPOINT.json)
- [Owner acceptance contract](SnowTruckGarage/2026-11-27/OWNER_ACCEPTANCE.md)

The associated concept-art package is `Docs/Design/SnowTruckGarage/2026-11-27/`; its art manifest and independent visual evidence own selected filenames and review status. The reusable native project is `tools/havenline/vehicle_rules/`. Consult the final delivery evidence for actual test counts; this document assigns no unobserved pass or game-wide score.

## Key decisions

| Area | Current feature contract |
|---|---|
| Unlock and price | Capability-gated; garage first, then a distinct truck purchase plot inside camp. Every material and its full acquisition chain must be available. No fixed level or unmeasured final price is invented. |
| Cargo | Every ordinary portable resource type; exact logical quantities with no gameplay capacity. Representative stacks are bounded independently of inventory. |
| Deposit | Entire truck and blades parked inside the correct bay, stopped and blades stopped; one whole-cargo transfer to an operational linked all-resource warehouse ledger. |
| Unavailable destination | All cargo remains aboard with a visible hold and automatic retry when the destination is usable. No silent spill, partial loss or capacity upsell. |
| Destruction | Outside-camp cargo is lost once. A wreck fully inside camp uses persistent typed salvage as a selected default; the vehicle is still destroyed. |
| Driver | Truck cargo and player inventory are separate. Release the driver and restore valid controls; existing player recovery preserves personal inventory. No invulnerable or trapped driver state. |
| Camp layout | Garage door replaces an approved fence segment. Preserve two distinct usable bidirectional pedestrian openings, the centered furnace, initial character scale and snow outside camp. |
| Recovery | Damage-scaled material repairs for a surviving truck; a destroyed truck is repurchased at level 1. Both paths remain attainable without owning the missing truck. |
| Fuel | No fuel-consumption requirement is introduced by this package. A later fuel proposal needs an explicit decision and attainable recovery proof. |

The latest audit branch independently records the same request at `afc6d5da3a8605ba7baeb01b7bcc847c0a814347`. Its finite/full-destination partial-unload recommendation is reconciled here with an all-resource warehouse ledger and an all-or-hold transaction. Existing storage art assigns no numerical capacity, and the new user requirement is unlimited cargo with automatic garage deposit.

The wider gameplay gaps remain active: self-service customer baskets, worker bulk stocking and cash collection, constructive obtainable quotes, persistent threats, companion death and useful attacks, structure repair/rebuy, furnace recovery, full animation/audio, and actual-world saving. Their concrete next actions are retained in the [integration map](SnowTruckGarage/2026-11-27/INTEGRATION_MAP.md).
