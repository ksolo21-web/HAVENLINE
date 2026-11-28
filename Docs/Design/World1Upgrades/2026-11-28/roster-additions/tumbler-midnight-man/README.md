# Tumbler and Midnight Man — additive planning reconciliation

**Tumbler and Midnight Man add two distinct design identities to the tracked scope.** Tumbler is explicitly a World 1 vehicle concept. Midnight Man is a planned playable character; his world availability and unlock remain unspecified. Neither source establishes a playable implementation. This addition preserves the previous upgrade package and adds source-bound work requirements. [Source manifest](SOURCE_MANIFEST.json) · [Complete scope delta](SCOPE_DELTA.json).

## Counts and preservation

| Coverage | Historical snapshot | Reconciled tracked scope |
|---|---:|---:|
| Family records | 99 | **101** |
| Vehicle families | 1 | **2** |
| Human-actor families | 10 | **11** |
| Playable-character identities | 4 | **5** |
| Authored value ladders / stage proposals | 27 / 54 | **27 / 54 retained** |
| Reviewed presentation files / panels | 7 / 24 | **7 / 24 retained** |

These are inventory counts, not counts of approved upgrades or World 1 unlocks. The historical **38 conditional briefs** remain historical; the two additions have **upgrade disposition pending**. No new tier, render, runtime ID or numeric unlock is authored here. `tumbler` and `midnight_man` are local planning identifiers only. “Man” is Midnight Man’s alias, not another family.

The [99-family census](../../WORLD1_UPGRADE_CENSUS.json), [27-ladder plan](../../PURCHASE_VALUE_UPGRADE_PLAN.md), seven-image evidence and all earlier receipts remain intact. The 10-world × 50-level plan, storage-house improvements, multiple pets/survivors and selected resource/conveyor scale remain binding.

## What the new sources actually define

### Tumbler

The [pinned vehicle design](https://github.com/ksolo21-web/HAVENLINE/blob/5b5ae75a6bd74d708eceb6d8a4837d977bcd5cb3/Docs/Design/WorldVehicles/2026-11-28/README.md) describes a **planned armored resource hauler**, distinct from Snow Truck. Twin flat horizontal front cutters attack eligible enemies, chop trees and break every mineable rock type while retaining the existing paid-camp cutter safety rule.

Its targeting automatically acquires **up to 10 distinct eligible enemies**. Firing requires the player’s **Launch** input; missiles follow their assigned targets. A **shared three-second cooldown starts after a successful volley**. These numbers come from the published baseline design, not new tuning in this delta.

An armored rear hatch above the turbine holds harvested resources. Typed custody, exactly-once warehouse unloading and existing inside/outside wreck rules are retained. The depicted logs and mineral crate are examples, not a capacity limit. Unlock, cost, power source, balance and final runtime assets remain open. The broader [vehicle-economy context](source-text/VEHICLE_ECONOMY.txt) does not override Tumbler’s explicitly unspecified power source.

The older package’s generic “vehicle baseline” refers to **Snow Truck**. Tumbler does not automatically inherit its fuel requirement, unlimited cargo, geometry or proven garage fit. VC01/VC02 remain unresolved; exactly-once custody and named paid-camp safety do not settle those broader transfer/blade-policy conflicts.

### Midnight Man

The [pinned character design](https://github.com/ksolo21-web/HAVENLINE/blob/527175227fe323d866109853e7217c6505cff080/Docs/Design/CharacterTurnarounds/2026-11-28/midnight-man/README.md) adds a **planned playable lead** without replacing the existing four. It grants no model, rig, runtime roster slot, unlock or balance approval. His batarangs automatically select eligible enemies, trees or mineable rocks; throw trigger, priority and cadence remain undecided.

| Combo concept | Source sequence and purpose |
|---|---|
| Sweep | Jab → cross → sweeping kick; push back nearby enemies. |
| Breakthrough | Advancing punch → rising knee → heavy stomp; stagger a durable target. |
| Rebound, proposed finisher | Side-step kick → spinning backfist → auto-targeted batarang; create space and finish at range. Hybrid versus all-melee remains unresolved. |

Damage, range, controls and unlock placement remain open. His kit is character-specific: standard player orbiting axes and survivor two-handed tools remain unchanged. He is not a survivor, pet or extra companion slot. [Playable roster source](source-text/PLAYABLE_ROSTER.txt).

## Task impacts and assignment gap

The JSON preserves each affected task’s exact existing name and dependency array. It activates no task and changes no ownership.

| Existing task IDs | Reconciliation |
|---|---|
| **T53, T32** | Owned local transport and World 1 content coverage for Tumbler; preserve later inter-world obligations. |
| **T12, T14, T43** | Identity, availability, save migration and cloud continuity. |
| **T07, T55** | Explicit Launch and accessible controls; resolve Midnight Man’s input decisions. |
| **T08, T09, T21** | Typed cargo, harvesting, targeting, combat contacts and accepted-event receipts. |
| **T03, T11, T20** | Camp/garage/storage compatibility; T20 retains customer-vehicle responsibility. |
| **T06, T59–T61** | Preserve the four existing character-specific gates; none approves Midnight Man. |
| **T33, T64** | Future attainable acquisition and upgrade-value proof. |
| **T54, T56, T58, T62–T64, T66–T70** | Applicable presentation, performance, economy, regression and exact-release acceptance. |

Midnight Man needs a **named, unassigned implementation and independent rig/action review work item**. No T-number is invented; T71–T80 remain source gaps. T53’s existing later-world dependencies also require explicit release-gate reconciliation rather than a silent graph edit.

## Next deliverables and acceptance

First inspect the two pinned turnaround images. Their Git identities are recorded, but this reconciliation has not visually inspected or approved them.

Then prepare separate source-faithful appearance/value briefs: Tumbler’s hull, cutters, volley, cargo and storage/garage fit; Midnight Man’s identity, gear, three combo clips, throw and combat/harvest interactions. **Existing cutters, volley, cargo, batarangs and combo concepts are baseline abilities, not newly unlocked upgrade benefits.** Any future purchased stage needs a real additional gain, visible mechanism, requirements, flow/access consequences and tradeoff. No tier or price is selected here.

Native evidence must cover every mineable type including slate/coal; 0/1/10/>10 volley targets; no launch without input; blocked unloading and save/reload; actual rig and full action cycles at normal camera; correct combat/harvest targeting; and one harvest receipt per accepted event. The JSON supplies dependency-aware milestones, 14 requirements and 16 acceptance checks. The exact-candidate independent document-review result is recorded separately in `INDEPENDENT_REVIEW.json`; visual, native and release gates remain open.
