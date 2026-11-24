# T11 frozen scope — Camp construction and visual upgrade system

## Required outcome

Build the authored camp-construction content layer that consumes the approved T10 World Transformation Framework without changing its transaction semantics. T11 owns the actual camp construction pads, authored camp structures/materials, visual construction/upgrade stages and readable before/ready/transition/after presentation. The result must reproduce the authoritative Havenline reference language: a construction pad in the winter field leads to a fenced warm work area with a central heated vessel/fire, stock pads/counter space, clear gates/lanes and later visibly improved camp states.

T11 is content and presentation work. T10 remains the authority for transform eligibility, exact-once cost/debit/state transitions and component recovery. T12/T13 own progression architecture/difficulty and T15+ own customers, later production, combat and defense systems.

## Mandatory requirement IDs

- **T11-R01 — Authored construction stages.** Every shipping camp state is an authored, reviewable state with stable `camp_state_id`, explicit T10 recipe binding, presentation key and asset manifest. Primitive/debug stand-ins, invisible construction and rate-only upgrades are forbidden.
- **T11-R02 — Reference-grounded first camp.** The initial constructed camp must visibly establish the fenced warm/brown work floor, readable gate/access lane, central heated vessel/fire zone, stock-pad/counter area and the compact ground-pad language seen in Reference B. T05-approved station/prop assets may be reused; T11 must not silently replace or mutate T05 source assets.
- **T11-R03 — Ground-pad contextual interaction.** Construction/upgrade is triggered through the existing movement/proximity/context language. T11 may show an in-world cost/readiness pad and short transition feedback, but may not add a required build button, large management menu, manual inventory grid or control-heavy placement mode.
- **T11-R04 — T10 exact-once consumption.** All T11 construction/upgrade commits call the published T10 transform interface. T11 presentation never debits resources/currency, advances progression or writes authoritative transform state directly. Replay/double-trigger/reload cannot double-charge or duplicate a structure.
- **T11-R05 — Truthful staged presentation.** `locked`, `ready`, `preview`, `committing`, `complete` and blocked/error states map to visibly truthful camp presentation. Before/after states must be unambiguous at gameplay camera scale; transition effects may decorate but cannot conceal the actual final geometry/state.
- **T11-R06 — Distinct visible upgrades.** Every registered camp upgrade must produce a meaningful visible world change rather than only a hidden stat/rate change. Distinct stages preserve functional gates/lanes and cannot collapse separate progression actions into one generic upgrade.
- **T11-R07 — Price/source discipline.** Do not invent shipping costs from video labels or unrelated historical actions. Every shipping T11 recipe must cite an authoritative design/historical source or an explicit approved tuning record. The observable fishing-upgrade example and unrelated furnace/barricade costs are not reusable evidence for generic camp prices. Test-only fixtures must be clearly marked non-shipping.
- **T11-R08 — Navigation and camera continuity.** Construction and every upgrade preserve traversable player/helper routes, gate clearance, T04 camera readability and T07 automatic-context behavior. No stage may trap the player, close a required lane, force camera clipping or make actionable pads unreadable.
- **T11-R09 — Physical-loop continuity.** T11 consumes only T10-authorized delivered/available costs and may not bypass T08 carrying/stockpile truth or T09 acquisition/delivery. Construction does not grant hidden resources, delete unrelated stock or alter harvest yields/timing.
- **T11-R10 — Content/system boundary.** T11 supplies camp recipe registrations, presentation bindings and authored camp assets without changing `world_transform.gd`, T10 idempotency/atomicity rules or shared integration-only simulation files. If the public T10 interface is insufficient, raise a ChangeRequest instead of editing T10-owned runtime from T11.
- **T11-R11 — Exclude later feature ownership.** T11 does not implement customer models/queues (T15), fishing/food chains (T16+), weapon upgrades/hostiles (T21), functioning defenses (T22), Level 1–100 architecture (T12), Challenge Director (T13) or global save/versioning (T14).
- **T11-R12 — Recovery-compatible content identity.** Camp state/recipe/presentation IDs are stable and deterministic so T10 component snapshots and later T14 persistence can reconstruct the same authored camp stage without duplicate spawning or asset ambiguity.
- **T11-R13 — Adaptive readable evidence.** Required evidence covers gameplay, overhead, side/three-quarter and detail views, the construction/upgrade sequence, blocked/ready states and adaptive phone/tablet/foldable layouts. Native 3840x2160 scale-1 capture is required where the current development evidence pipeline supports it; it is not physical-device certification.
- **T11-R14 — Bounded presentation cost.** Static completed camp stages do not rebuild every frame. Construction effects, pad indicators, materials, geometry and collision stay within published performance/headroom budgets and release cleanly after transitions.
- **T11-R15 — Dependency truth.** T11 production implementation may not enter `ASSIGNED`/`BUILDING_ISOLATED` until T05 and T10 are both `APPROVED`, with T10 integrated on the authoritative branch. Governance packet/tooling/workflow preparation may complete while T09/T10 runtime work is unfinished.
- **T11-R16 — Acceptance gate.** Required critics are C2/C3/C4/C6 exactly as registered. Every mandatory dimension must be strictly greater than 9.0 unrounded, target 10/10; all applicable G1-G14 gates and impacted approved-task regression must pass with zero unresolved mandatory defects.

## Explicit exclusions

- No changes to T10 transaction, idempotency, atomicity or recovery semantics.
- No direct edits to T08 inventory/carrying rules or T09 harvesting behavior.
- No new customer/NPC population, fishing/food production, weapon/combat, defense-tower functionality, companions, biomes, monetization, cloud identity or release-certification work.
- No unrestricted freeform building system or manual structure-placement mode.
- No invented shipping prices/timings solely to make a test pass.
- No global save-versioning implementation; T14 owns it.

## Planned ownership reservation

The T11 isolated builder will own only the following disjoint paths once activation is legal:

- `HavenlineGodot/scripts/camp_construction.gd`
- `HavenlineGodot/scripts/camp_construction_view.gd`
- `HavenlineGodot/data/camp_upgrade_recipes.json`
- `HavenlineGodot/assets/camp_upgrades_v1/**`
- `HavenlineGodot/tests/test_task11_camp_construction.gd`
- `HavenlineGodot/tests/test_task11_integration.gd`
- `HavenlineGodot/tests/capture_task11_camp_upgrade.gd`
- `Docs/Production/T11/**`
- `tools/havenline/task11/**`
- `.github/workflows/havenline-task11-*.yml`

T11 may reference but not mutate approved T05 assets and T10 runtime. Shared shipping wiring (`main.gd`, `simulation.gd`, canonical registries) remains integration-owner work.

## Required acceptance evidence after activation

- Exact post-T10 integration base, candidate hash and authorized changed-file manifest.
- Machine-readable camp-state/recipe/presentation manifest with stable IDs and shipping-vs-test pricing provenance.
- Initial field/pad state and fully constructed first-camp state matching the authoritative camp visual language.
- At least one complete structural visual-upgrade sequence using the T10 lifecycle, with every registered shipping stage represented in evidence.
- Exact-once proof for proximity re-entry, repeated trigger, duplicate transaction, stale state and reload/reconstruction cases.
- Route/collision matrix proving player/helper lanes, gates and pads remain reachable through every state.
- T04 camera and T07 contextual-control regression; no new required action button/menu.
- T08/T09 resource conservation compatibility through T10 commit paths.
- Gameplay, overhead, side/three-quarter, detail, blocked, ready, transition and complete views; adaptive phone/tablet/foldable coverage and native 3840x2160 scale-1 evidence where applicable.
- Geometry/material/collision/performance metrics for all authored camp states and transition cleanup.
- Full impacted T01-T10 regression after integration.
- Independent C2/C3/C4 review plus quantitative C6; every mandatory dimension strictly >9.0 unrounded, target 10/10.
