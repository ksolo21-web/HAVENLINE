# T09 frozen scope — Harvesting and automatic acquisition

## Required outcome

Replace the gathering-side orbiting/swiveling placeholder with a polished,
truthful automatic harvesting loop for the existing opening resources. When the
player approaches an eligible source, T07 selects the action, the correct authored
tool is attached to the T06 contact contract, the source reacts at the exact
simulation impact beat, and the committed unit flows through T08 into the visible
carried stack. Simulation remains the sole authority for quantities, depletion,
respawn and rewards. No manual gather control or logical carrying limit is added.

## Frozen opening-resource decisions

- `wood` — chop with an authored axe using `human_player_chop`.
- `stone` — mine with an authored pickaxe using `human_player_mine`.
- `metal` — mine the existing ore source with the same authored pickaxe using
  `human_player_mine`.
- `fuel` — dismantle the existing fuel-salvage source with an authored compact
  salvage pry tool using `human_player_dismantle`.

These decisions resolve the T09 placeholders in
`RESOURCE_ACTION_REGISTRY.json`. They do not add new resources, recipes, tools,
prices or resource yields.

## Mandatory requirement IDs

- **T09-R01 — Registry closure.** `wood`, `stone`, `metal` and `fuel` have complete,
  production-ready collection method, tool, player animation, carry visual and
  destination records. Exact registry hashes are bound into candidate evidence.
- **T09-R02 — Automatic contextual selection.** T07 remains the only player action
  selector. Movement/proximity/facing/hysteresis chooses the correct registered
  gather action without a pickup, tool-cycle, gather or inventory button.
- **T09-R03 — Authored finished tools.** Provide polished stylized axe, pickaxe and
  salvage-pry assets that match Havenline's blue/orange/brown material language.
  No primitive/debug tool, invisible tool, generic cube or combat weapon fallback
  may pass as finished presentation.
- **T09-R04 — Exact attachment and contact.** Tools bind to the published T06
  hand/two-hand contacts with correct grip, facing and target reach. They may not
  float, reverse, penetrate the body, miss the target or remain attached after the
  action ends, cancels, switches, reloads or the actor becomes hidden.
- **T09-R05 — Authoritative impact beat.** Anticipation, contact and recovery remain
  synchronized to T06 action progress and the single committed simulation gather
  event. Presentation never grants, debits, duplicates, predicts or replays a unit.
- **T09-R06 — Source-specific response.** Wood shows bounded chips and trunk impact;
  stone/metal show differentiated rock/ore strike feedback; fuel salvage shows a
  restrained dismantle/spark response. Feedback is pooled, deterministic, readable
  at gameplay scale and stops immediately when the source is depleted or invalid.
- **T09-R07 — Visible acquisition continuity.** Every committed unit uses T08's
  source-to-actor transfer and updates the correct physical carried stack exactly
  once. Interrupted, replayed, stale and malformed events fail closed without
  changing logical or visible counts.
- **T09-R08 — Source and depletion truth.** The presented target identity, resource
  type, remaining/depleted state and respawn visibility agree with simulation.
  Visual compression or effects may not make an empty source appear harvestable.
- **T09-R09 — Actor boundary integrity.** T09 proves the `player_lead` harvesting
  set and compatibility with registered core-helper/survivor capabilities without
  silently reusing the player's final motion for those roles. T23/T31 and T59-T61
  still own their distinct final work motion and rig proof.
- **T09-R10 — C5 motion quality.** Full chop, mine and dismantle cycles, entries,
  cancellations and recoveries show stable feet/toes/knees/hips, credible weight
  transfer, clean shoulders/elbows/hands, secure tool grip, target contact and no
  body/tool/gear clipping at real-time and slow review speed.
- **T09-R11 — Adaptive readability and persistence.** Phone, tablet and foldable
  gameplay states keep actor, target, tool, source feedback, T08 transfer and carried
  stack readable without obscuring joystick/status/context hints. No new required
  save field is introduced; presentation reconstructs safely from current state.
- **T09-R12 — Bounded performance and future boundary.** Tool instances, chips,
  sparks and impact pulses are pooled/bounded; unchanged state does not rebuild
  nodes; integrated frame/draw/geometry/memory deltas preserve full-game headroom.
  Do not implement T10 world transformation, T16 fishing, T19 crops, T21 combat
  weapons, helper/survivor final motion, new regions or release certification.

## Explicit exclusions

- No manual gather/pickup/tool-selection button, grid inventory, capacity,
  encumbrance, energy wall or action menu.
- No edits to simulation quantities, yields, respawn timing, T07 ranking, T08
  conservation/carry rules, approved T01-T08 assets or Character 1 source GLB.
- No combat weapon or radial/orbiting attack replacement; T21 owns combat.
- No fish, wheat, new resource, recipe, economy, station upgrade, world
  transformation, helper/survivor final animation, cloud or LiveOps work.
- No unfinished APK handoff, whole-game approval claim or physical-device 4K/60
  certification claim.

## Ownership and integration wiring

The isolated builder owns `@reservation:T09`: `harvesting_v1` assets,
`harvest_presentation.gd`, T09 tests/capture/evidence tools/docs and its workflow.
`main.gd`, `simulation.gd`, `character1_motion.gd`, `context_director.gd`, T08
modules and the canonical registries remain protected/integration-owned. Shipping
wiring or a required upstream contract edit uses a structured change request and
is applied only by the integration owner.

## Required acceptance evidence

- Exact base/candidate hashes, authorized changed-file manifest and current
  resource/actor/animation/reference hashes.
- Isolated asset turntables for axe, pickaxe and salvage pry tool; in-hand front,
  rear, left, right, three-quarter, overhead and close grip/contact views.
- Matched gameplay sequences for wood, stone, metal and fuel showing approach,
  T07 focus, anticipation, exact impact, source response, committed T08 transfer,
  stack update, cancel/re-enter, depletion and respawn boundary.
- Full real-time and slow chop/mine/dismantle cycles and transitions, including
  feet/toes/knees/hips/shoulders/elbows/hands/tool/target/gear clipping proof.
- Interrupted/replayed/stale/malformed event cases; lead switch, hidden actor,
  save/reload/migration/recovery; six adaptive device cases and native
  3840x2160 scale-1 evidence.
- Full T01-T08 impacted regression, resource/actor contract proof, pooled-effect
  bounds and integrated C6 metrics.
- Independent C2, C3, C4 and C5 plus quantitative C6. Every mandatory dimension
  must be strictly greater than 9.0 unrounded, target 10/10, with zero unresolved
  mandatory defects.
