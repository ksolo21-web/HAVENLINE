# T08 frozen scope — Visible inventory, physical carrying and transfers

## Required outcome

Turn the existing conserved logical inventory into a truthful, readable physical
loop. Every committed acquisition is shown moving from its source to the correct
visible actor stack; every committed deposit/build/repair transfer is shown moving
from that actor to its real destination; carried and stored quantities remain
legible without imposing a logical capacity or adding a manual inventory control.
Simulation remains the sole authority for resource counts and outcomes. T07 remains
the sole context/action selector and T06 remains authoritative for Character 1
motion.

## Mandatory requirement IDs

- **T08-R01 — Unlimited logical inventory.** Never cap, discard, round, reorder or
  mutate simulation inventory for presentation. Counts up to the accepted save
  envelope remain exact through gather, transfer, save and restore.
- **T08-R02 — Registered resource coverage.** Provide deterministic authored carry
  presentation for current production resources `wood`, `stone`, `metal` and
  `fuel`. Future registered resources fail visibly until their owning task freezes
  an authored carry profile; no generic cube or silent fallback is allowed.
- **T08-R03 — Physical carried stacks.** Use the approved T05 authored resource
  meshes to build stable, upright, readable stacks attached to the carrying actor.
  Stack composition must match the actor's logical resource composition.
- **T08-R04 — Bounded visual compression.** Show small loads exactly and large loads
  through deterministic tiers/height/compression while retaining the exact logical
  count in presentation metadata. Visual budgets may cap instances, never value.
- **T08-R05 — Automatic transfer paths.** A committed gather/worker-gather event
  travels source → actor; committed deposit/build/repair/customer transfer events
  travel actor → destination. Paths are pooled, bounded, arc smoothly and identify
  resource, actor, destination and direction.
- **T08-R06 — Conservation and authority.** Presentation consumes committed events
  only. It cannot grant, debit, duplicate or replay inventory. Each simulation beat
  produces at most one matching visual receipt and stale/invalid events fail closed.
- **T08-R07 — Destination stockpiles.** Camp storage/furnace materials are shown as
  grounded authored stockpiles whose resource composition and compressed count
  derive from `sim.stored`; defense/build delivery remains visibly destination-bound.
- **T08-R08 — Multi-actor integrity.** Selected lead, core companions and presented
  survivor helpers retain separate stack identity. Lead switching transfers the
  existing logical cargo view without duplication; hidden/unready actors never gain
  a secret visible or logical stack.
- **T08-R09 — Context compatibility.** Preserve T07's movement/proximity-driven
  contextual action contract and T06's action motion. T08 adds no inventory menu,
  transfer button, pickup button or permanent control.
- **T08-R10 — Persistence derivation.** T08 adds no required save field. Fresh,
  current, previous, interrupted, reload, migration and rollback recovery rebuild
  physical stacks deterministically from authoritative counts without duplicate
  grants.
- **T08-R11 — Readability and adaptation.** At approved T04 gameplay scale, phone,
  tablet and foldable layouts show resource identity, direction and meaningful load
  change without covering the actor, target, joystick, status or contextual hint.
- **T08-R12 — Bounded performance and future boundary.** Pool resource pieces and
  transfer flights, cap visible instances and active flights, expose metrics, and
  preserve full-game headroom. Do not implement harvesting/tools (T09), new resource
  acquisition, construction upgrades (T11), economy/service systems, weapons,
  additional actors, cloud, LiveOps or release certification.

## Explicit exclusions

- No logical inventory limit, weight penalty, encumbrance or energy wall.
- No grid inventory, drag/drop, item selection, manual pickup/deposit or action
  button.
- No new resource or recipe and no claim that unresolved fish/wheat carry art is
  production-ready.
- No edits to approved T01–T07 task-owned assets or modules.
- No direct isolated-builder edits to `main.gd`, `simulation.gd`,
  `population_view.gd`, `outpost_simulation.gd`, `outpost_view.gd` or
  `reference-contract.json`.
- No whole-game, player APK or physical-device native-4K/60 completion claim.

## Ownership and integration wiring

The isolated builder owns `@reservation:T08`: carry-stack, destination-stockpile
and transfer-feedback presentation modules; T08 tests/capture/evidence tools/docs;
and its task workflow. Shipping wiring in `main.gd` or another integration-only
module requires a structured change request and integration-owner implementation.

## Required acceptance evidence

- Exact base/candidate hashes, authorized changed-file manifest and the pinned
  resource/actor/animation/reference registry hashes.
- Deterministic count-to-layout tables for 0, 1, small mixed loads, visual-budget
  boundary, very large counts and maximum accepted save counts.
- Source → player, source → helper, player → furnace/storage, helper → storage,
  player/helper → build target, interrupted/replayed/invalid-event cases.
- Matched normal gameplay, close/detail, front/rear/side/three-quarter/overhead,
  phone/tablet/foldable and native 3840×2160 scale-1 evidence.
- Continuous normal-speed transfer sequences, exact conservation traces, pool and
  active-flight bounds, save/device matrices, and full T01–T07 impacted regression.
- Required critics C2, C3, C4 and C6; every mandatory score strictly greater than
  9.0 unrounded with zero unresolved mandatory defects.
