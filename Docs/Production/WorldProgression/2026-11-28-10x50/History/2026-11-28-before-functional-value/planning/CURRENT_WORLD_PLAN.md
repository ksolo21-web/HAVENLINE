# Havenline — 10 worlds, 50 levels each

## Current direction

**The owner has fixed the campaign structure at 10 worlds × 50 local levels = 500 planned level positions.** T12 and T32 must no longer be summarized as a 100-level campaign and a 10-level opening world. This package records forward planning and World 1 upgrade-render scope; it does not implement the progression or approve the game.

The current separate [World-Progression source](https://github.com/ksolo21-web/HAVENLINE/blob/5862b89c1663cacc0cbb84bfaba438d1459cfdb6/Docs/Production/Build13Audit/World-Progression.md) already selects World 1 as the initial release and later connected updates for Worlds 2–10. Its earlier tentative fifty-level wording is superseded by the owner's latest fixed-count instruction. Its old ten-level bands are preserved as historical design inputs, not current ranges.

## Worlds and task ownership

| World | Theme | Existing task | Local levels | Delivery |
|---|---|---|---|---|
| 1 | Frozen Home Camp | T32 | 1–50 | World 1 release |
| 2 | Forest and Lakeshore | T44 | 1–50 | Later connected update |
| 3 | Desert Canyons | T45 | 1–50 | Later connected update |
| 4 | Underwater Refuges | T46 | 1–50 | Later connected update |
| 5 | Sky Islands | T47 | 1–50 | Later connected update |
| 6 | Volcanic Forge | T48 | 1–50 | Later connected update |
| 7 | Swamp Boardwalks | T49 | 1–50 | Later connected update |
| 8 | Ruined Settlement | T50 | 1–50 | Later connected update |
| 9 | Underground Mines | T51 | 1–50 | Later connected update |
| 10 | Alien Frontier | T52 | 1–50 | Later connected update |

The table retains world themes/order and existing task identities. T71–T80 remain missing definitions; 500 gameplay positions do not create new numbered production tasks. Exact new unlock levels, region milestones and the complete 500 authored outcomes have not been created by this package.

## What changes in the task plan

- **T12:** ten-world architecture, fifty local levels per world, coherent milestones, stable interfaces and versioned progression identity.
- **T32:** complete World 1 local Levels 1–50 and a continuing frozen-world sandbox, including the garage/truck/material/fuel additions.
- **T44–T52:** one later world each, local Levels 1–50, with their own resource and route decisions.
- **T33:** an attainable World 1 economy and later connected campaign; length must not be manufactured by multiplying prices or grind.
- **T53:** separate current local vehicle/route scope from later inter-world travel while preserving the connected-network obligation.
- **T62/T63/T65/T67–T70:** explicitly distinguish World 1 release acceptance from later-world and full-campaign acceptance. All applicable evidence gates remain; the existing graph is not silently rewritten.

The complete [80-row scope delta](TASK_SCOPE_DELTA_T01_T80.md) includes 20 direct changes, 43 indirect verification rows, 7 rows with no identified core change and 10 source gaps. Historical lifecycle labels in its JSON are source snapshots, never approvals of this new candidate.

## World levels, equipment levels and appearance stages

A world level describes progression through that world. An equipment level describes that asset's upgrade state. An appearance stage describes a visible model/material/configuration change. A purchased boundary tier, a damaged state, an operating state and a cosmetic variant are also different concepts.

**Fifty world levels do not require fifty separate models of every asset.** The current World 1 work must inventory each genuinely upgradeable object, preserve its selected baseline, identify the appearance changes already covered by renders, and produce references for the missing changes. Exact asset caps and which equipment levels trigger a new model must follow an explicit asset contract; no new numbers are inferred from old image labels or decorative A/B/C variants.

For each selected visual stage, record the real functional difference, footprint/service clearance, machine ports, conveyor height and route, player/resource scale, required damage/repair/empty/full/active states, owner task and actual review status. An upgraded object must still work in its camp layout. New renders are concept/reference evidence, not native model, animation, throughput or device approval.

The separate source's five World 1 planning groups—establish camp, open supply routes, grow trade/production, defend expansion and run a resilient settlement—are useful pacing inputs across local 1–10, 11–20, 21–30, 31–40 and 41–50. They do **not** freeze specific truck, garage, pet, fishing, crop or equipment unlock levels. Preserve the small meat-based Level 1 opening; later World 1 content does not automatically move into that first level.

## Garage, truck and resource precedence

The garage must be built before the player can buy the snow truck. Its door replaces a fence section while retaining two usable pedestrian openings. The truck has HP, low horizontal working blades and unlimited typed resource cargo. Destruction outside camp loses the remaining truck cargo once; destruction inside camp leaves recoverable typed salvage. Paid repair/replacement and a reachable on-foot recovery path remain required.

The owner-confirmed fuel expansion, recorded in the [vehicle-economy rule](https://github.com/ksolo21-web/HAVENLINE/blob/69bd3eb921ce18838795b3ce21b232ec6e3b54b6/Docs/Production/VehicleEconomy/2026-11-27/SUPERSESSION.md), requires **low fuel use**. It supersedes earlier no-fuel/open-fuel wording. Oil extraction/refining, coal and iron ore → bars → sheet metal are meaningful World 1 inputs to expensive processed-resource construction. Fuel depletion stops propulsion/tools safely; it is not destruction. Exact tank/burn figures and prices are fixtures awaiting playtest balance.

Two policies conflict across the pinned sources: the planning audit permits partial warehouse receipt and says blades are off inside camp, while the dedicated vehicle package specifies whole-load transfer or HOLD and allows deliberately authorized hostile defense with safe default travel. This task does not establish the underlying decision order, so both policies remain recorded for authority reconciliation. No policy is silently selected or changed. The shared render constraints are sufficient here: parked/docking/refuel/service/unload blades are inactive, cargo and operating-tank fuel remain distinct, and stock is never duplicated or silently discarded by an image.

## Identity and migration boundary

The proposed interface uses a world identity plus local level. A derived planning ordinal may be calculated as `(world_index − 1) × 50 + local_level`, covering 1–500. This is a data/interface proposal, **not an approved UI numbering choice or a completed save migration**. The concrete ID namespace, old-save mapping and global display still require T12/T14 reconciliation.

Earlier 100-level data and proofs are preserved. Do not multiply old unlock numbers by five, rewrite receipt identities, reprice accepted quotes, erase paid upgrades or declare the old 100 authored outcomes to be 500 new ones. [Migration requirements](MIGRATION_REQUIREMENTS.md) identify the actual schema/code changes needed.

## Acceptance and next action

Planning-package acceptance requires an exact ten-world/fifty-local-level contract, all 80 task dispositions, preserved dependencies and historical evidence, explicit source precedence, a World 1-only render boundary, no invented asset caps/unlocks, and a concrete migration ledger. Run `python verify_plan.py` for structural checks, then obtain an independent review of the package and the actual render outputs.

Next: complete the World 1 upgrade-asset census, generate/review missing appearance references, publish the reviewed package without touching active gameplay, and route the versioned progression migration to the current gameplay owner. [Resumption checkpoint](CHECKPOINT.json) records remaining obligations. No runtime or shipping gate is passed by this document.
