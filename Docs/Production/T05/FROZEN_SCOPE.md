# T05 frozen scope — production station and prop kit

## Required outcome

Deliver a cohesive authored 3D station and prop kit that replaces generic
prototype staging with the bright, polished, sculpted Havenline visual language
shown in both authoritative recordings. The kit must support the established
frozen camp and lakeshore layouts without changing the approved T01–T04
environment, camera, routes or gameplay contracts.

T05 is the reusable visual and attachment foundation for later production,
customer, construction and defense tasks. It does not implement those systems.

## Mandatory requirement IDs

- **T05-R01 — Heated vessel/furnace family.** Provide a central warm production
  vessel with a readable heat chamber, insulated body, chimney/vent language and
  authored upgrade-ready attachment points. It must read clearly at normal
  gameplay scale and hold up in close-up.
- **T05-R02 — Counter family.** Provide modular service/processing counters with
  distinct staffed side, customer side, stock surface and transfer sockets.
- **T05-R03 — Ground-pad family.** Provide build, upgrade, input, output, stock
  and payment pad variants whose purpose remains distinguishable by silhouette,
  trim color and in-world icon socket without relying on large text or HUD.
- **T05-R04 — Fishing fixtures.** Provide a shoreline rod/rack fixture, intake
  fixture and fish-container props suitable for the approved lakeshore edge.
- **T05-R05 — Processing fixtures.** Provide modular intake, cooker/processor,
  output and conveyor-ready fixtures. Static belt modules and connection sockets
  are in scope; automated transport and processing behavior remain later tasks.
- **T05-R06 — Defense fixtures.** Provide a timber-and-metal defense platform,
  weapon socket and supply/repair props. Firing, targeting and damage behavior
  remain T22.
- **T05-R07 — Resource prop family.** Provide reusable authored wood, stone,
  metal, fuel, fish, cooked-food, money and crate/basket pile modules that can
  form legible small and tall physical stacks in later tasks.
- **T05-R08 — Coherent art language.** Use clean sculpted shapes, blue/orange/
  yellow machinery accents, warm timber/metal, snow-aware contact treatment and
  shared materials. No debug/default materials or crude primitive stand-ins may
  pass as finished art.
- **T05-R09 — Stable sockets and bounds.** Every kit entry exposes deterministic
  input/output/worker/customer/upgrade/FX sockets as applicable, plus finite
  footprint, visual bounds and clearance metadata.
- **T05-R10 — Route and camera compatibility.** Nominal camp and lakeshore
  arrangements preserve approved T03 gates/work lanes and remain readable under
  the approved T04 shipping camera across the landscape device matrix.
- **T05-R11 — Deterministic catalog.** A machine-readable catalog binds each
  station/prop ID to its asset, materials, sockets, footprint, intended later
  system and asset hash; duplicate IDs or missing assets fail closed.
- **T05-R12 — Performance headroom.** The nominal integrated kit stays inside
  its assigned production/interactable budget with material reuse, bounded
  geometry and no active physics, skeleton or animation cost added by T05.

## Explicit exclusions

- No fishing, harvesting, processing, conveyor transport, customer service,
  payment, inventory, construction, upgrade, combat, defense or economy logic.
- No moving goods, active heat simulation, firing weapons, damage, rewards,
  prices, recipes, production rates or save-schema changes.
- No character, NPC, companion, animation, HUD, control or input changes.
- No edits to approved T01–T04 runtime assets/behavior or the authoritative
  `reference-contract.json` values.
- No T06+ implementation and no physical-device 4K/60 certification claim.

## Ownership and integration wiring

The isolated builder owns `@reservation:T05`. Shipping placement requires only
the minimum approved call-site wiring in integration-only runtime paths. The
builder must submit a structured change request; only the integration owner may
apply that wiring after the isolated candidate passes ownership review.

## Required acceptance evidence

- Catalog completeness and exact asset/hash/socket/bounds audit for T05-R01–R12.
- Front, rear, left, right, three-quarter and close-detail views of every station
  family, with representative variants grouped only when all remain legible.
- Normal gameplay-scale camp and lakeshore arrangements using the approved T04
  camera, including ground contact, worker/customer approach clearance, input/
  output orientation and T03 route preservation.
- Bright reference comparison plus night and blizzard condition views.
- Required landscape phone/tablet/foldable composition states and at least three
  native 3840×2160 scale-1 frames. These frames do not certify physical FPS.
- Matched-camera contact sheet and deterministic quick-look gate before critics.
- Full T01–T04 impacted regression, task-specific tests and C1+C2+C6 review.
- Every mandatory score strictly greater than 9.0 unrounded, target 10/10, with
  complete coverage and zero unresolved mandatory defects.

