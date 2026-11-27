# Conveyor design checkpoint

## Intent
Build a compact, readable transport family connecting compatible machines, storage and sales without blocking camp movement. This is a proposed reference-art extension; existing images remain unchanged.

## Physical layout
- Production stays at the camp edge. Belts follow short local/perimeter routes.
- The storage front doors and apron stay clear. New utility dock is low on the LEFT wall below the existing high window. New prepared-food dock is low on the REAR wall below and separate from the high vent.
- Each dock contains independent inbound and outbound lanes. Each lane ends in a visible finite local tray/lift directly serving that perimeter bay. No belt secretly crosses the central aisle.
- The right fuel-service hatch is unchanged. Fuel, raw-food bins, hides and cargo/cash remain manually serviced through their original dedicated areas.
- Customer counter retains its timber table, four legs and shelf. Restock ends in a separate supported buffer beside the free stock end on the staff side. The register remains at the opposite end and faces the worker.
- Keep the heater centered, two gate corridors open, cooker controls accessible and customer queues outside the camp fence. Prefer no belt crossing of either primary gate corridor.

## Typed routes
1. Shore intake front discharge -> supported incline/bridge adapter -> cooker raw-input queue. Whole fish are source-observed input; the new side-feed adapter and revised cooker port are proposed.
2. Cooker cooked-fish output -> finite output buffer -> demand diverter. Compatible active counter first; surplus to prepared-food storage IN when space is reserved.
3. Prepared-food storage OUT -> request-controlled restock lane -> same counter buffer. Fresh-output and stored-output lanes join only through a gated merge. Only one source reserves each stock slot.
4. Future bread-like output and compatible cooked-food output -> SEPARATE input lanes of a future assembly station -> its own allowed-menu counter. Original A 56.5–59s supports this topology; exact ingredient identity, ratios and Havenline machine design remain proposals, not frozen recipes.
5. Saw/lumber station output -> utility buffer -> utility storage IN. Plank conversion is a proposed pairing; tool variants are alternatives, not mandatory serial machines.
6. Utility storage OUT -> a compatible workstation input or an explicitly permitted log/material counter. The stock does not automatically return to the same intake.
7. Quarry/extraction output -> typed material crate/feeder -> utility storage IN. Transport preserves item identity; no ore-to-ingot conversion is implied.
8. Fuel -> reserved manual fuel-service handoff -> central warming furnace. The heater is not a smelter and does not receive food.
9. Defense/weapon/workshop supply is a future typed extension, justified by ad presentation but without invented ammunition or crafting recipes. Existing racks, butcher tables and drying fixtures remain manual unless a new feeder/recipe is explicitly provided.

## Behavior proposal
- Carrier family + allowed SKU checked before release. Unknown or incompatible items remain at the source/reject pad; bounded reject pad full stops intake.
- Destination reserves a free slot before transfer. When it is full, a physical stop gate holds the next carrier. Backpressure stops upstream release.
- A machine reserves output space before starting a cycle. A two-input assembler reserves both accepted ingredients and output space together.
- Merge gates arbitrate one item at a time. Dispatch consumes an explicit request and a stock reservation; each item has exactly one transfer owner.
- No overflow deletion, duplication, infinite queues or permanent recirculation. Storage stock stays put until requested.
- Manual -> helper-assisted -> automated progression retains visible pickup, transport, processing and delivery.
- Numerical capacity/speed/cost, recipe quantities, precise world scale and runtime collision remain unapproved. Finite tray slot counts shown in concept art are illustrative.

## Deliverables / next step
Seven render studies plus exact SVG plan and machine-readable routing catalogue; evidence index for all registered videos and new primary sources. Independent critic checks this plan before generation, then reviews real render pixels and normal/full states. Archive all originals and repairs directly to an additive GitHub art branch after review.


## Preflight amendment
- Add D04B: a seventh, explicit dual-input assembly study based on A56–59s, with two separate ingredient magazines and one output; new Havenline machine design and controls are proposals.
- Utility dock indexes two bounded local compartments (timber/minerals); it never dumps a mixed pile. Transfer remains within the left shelving bay.
- D02 shows wrong-item held at source and normal/full stop states.
- Camp study reserves rear and left storage service space.

## Dock height clarification
Rear prepared-food sleeves serve the prepared-food shelf ABOVE the original closed raw-food cabinets and below the high rear vent. The exterior adapter adjusts to that shelf level. The low utility sleeves remain below the left window; neither dock uses the window, vent, fuel hatch or front door as its port.
