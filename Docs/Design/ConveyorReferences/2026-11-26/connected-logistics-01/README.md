# Havenline — connected camp logistics

**Design date: November 26, 2026 (America/Detroit).**  
A static reference-art and routing package for compatible machines, the upgradable storage house and customer service. Start with [GALLERY.md](GALLERY.md), then use the [directed route plan](design/D07-01-directed-routing.svg), [camp allocation](design/D07-02-camp-allocation.svg) and [machine-readable catalogue](design/routing-catalogue.json).

## The design decision

Use short, typed production routes around the camp perimeter. The first automated installation shown in D06 uses an explicit serial path: intake → cooker → storage → requested counter stock. The fuller D02/D07 upgrade adds direct compatible machine/counter feeds and controlled surplus storage, so storage becomes an optional buffer in that configuration. Neither phase uses an unlimited sink or a universal loop.

The visual family keeps Havenline's rounded blue/orange/silver machines, warm timber, dark carrying surfaces and compact winter camp. Belts have real supported transfer surfaces, corners and height adapters. Storage keeps its original facade and service features. The customer table remains a staffed timber counter.

## Seven reference studies

| Study | Purpose |
| --- | --- |
| D01 — Transport modules | Level straight, supported roller corner and cleated height adapter; opposing views expose the transfer surfaces. |
| D02 — Routing and buffers | Distinct diverter and gated merge; wrong-item hold; ready and destination-full buffer states. |
| D03 — Storage upgrade | Paired utility and prepared-food IN/OUT docks, exterior connections and local internal transfer cutaways. |
| D04 — Intake and cooker | The intake's front discharge feeds a proposed cooker side adapter; powered output reaches a finite receiving buffer. |
| D04B — Assembly | A proposed assembler with separate ingredient A/B magazines, a missing-input state and an output-full state. |
| D05 — Counter restock | A supported curved stock buffer stops beside the canonical counter; staff handoff, register, cash and customer face remain distinct. |
| D06 — First automation camp | Initial serial intake/cooker/storage/requested-counter route, centered warming furnace, clear doors/service access and two open bidirectional gates. The rotated house exposes its rear food docks. |

D07 adds exact editable SVGs and a catalogue containing **37 station dispositions, 25 directed routes and all 14 source equipment families**. D08 preserves the evidence, exact generation requests, source bindings, originals, revisions and independent reviews. The final selection and acceptance records bind the actual deliverables; an earlier planning status is not a final approval.

## How goods move

### First automated installation — D06

The camp render shows the bounded first stage: intake discharges whole fish into the cooker; its finished output enters reserved prepared-food storage; storage dispatches only against a compatible customer-stock request. The conveyor stops at the separate staff buffer, followed by manual table/service handoff and separate cash collection.

The [initial-deployment record](D06-initial-deployment.json) names nine station/endpoints and eight typed transfers, including the internal local shuttle and manual handoffs. It reuses the full catalogue's station/port definitions where applicable. A receiving-full condition stops upstream release while allowing an already valid outbound request to free storage space. There is no router or merge reservation in this single-source initial stage. The reviewed D02/D07 upgrade remains unchanged and adds the direct-fresh alternative described below.

For this initial placement, the house's rear dock faces the camera and its original front doors/apron face the far/north service aisle. The small water pocket is inside the camp, leaving a continuous outer floor strip around it; this site choice is a Havenline proposal. That strip connects the main gate route to the far-side house service aisle without requiring a belt crossing. The two large primary gates and the stone heater retain clear approaches. The D07 allocation illustrates the fuller upgrade and a different house/production placement.

### Expanded fish production and sales — D02/D07

1. The shore intake discharges whole fish at its front roller lip.
2. A supported adapter feeds the cooker's dedicated raw-input port.
3. Cooked output reaches a finite output buffer and a demand-controlled diverter.
4. Compatible active counter demand receives fresh output first.
5. Permitted surplus enters prepared-food storage IN only after space is reserved.
6. Prepared-food storage OUT releases compatible stock only against a counter request and reserved stock slot.
7. A gated merge arbitrates the fresh and stored sources. They cannot both claim the same destination slot.
8. The belt ends at a separate guarded stock buffer. A worker lifts stock onto the wooden table and serves customers. Cash uses its own pad.

These are proposed Havenline control rules. The references support the production and sales topology, not the exact reservation algorithm. Port orientation follows the machine's actual placement: rotating the machine rotates both ports and its service face, rather than swapping labels on the original geometry.

### Machine-to-machine assembly

Original A around 56.5–59 seconds shows differentiated cooked-food and bread-like feeds entering an assembly machine, then a short output belt reaching a vehicle counter. Havenline's proposed assembly study therefore uses **two separate accepted-input magazines**, not a mixed feed.

A cycle starts only when both required inputs and output space are reserved. Completion consumes the inputs once. Finished output dispatch then depends on the completed item and its owned destination reservation; it does not require ingredients that have already been consumed. Exact ingredient identities, quantities, production time and menu remain unfrozen.

### Timber and mineral materials

Utility transport is separate from food. A compatible extraction or processing output can feed a typed tray or feeder and the utility IN dock. The local indexed lift selects the timber or mineral compartment. Utility OUT dispatches only the requested class to an allowed workstation input or a counter that explicitly sells that material.

The proposed saw/lumber pairing does not turn all tool variants into a required serial line. A plank conversion is provisional. Quarry transport preserves the observed item form; it does not silently turn ore into ingots. Raw-looking log and meat sales appear in the owner references, so sales eligibility belongs to the counter's catalogue rather than a blanket processed-food-only rule.

### Manual and future connections

Fuel, the original raw-food cabinets, hides/fur, cargo/cash and undefined workshop or greenhouse outputs remain manual in this first conveyor upgrade. Racks, butcher fixtures and cookfires do not acquire invented automatic ports. Defensive resupply is a sensible future branch, but the ad evidence does not establish an ammunition recipe.

The central stone furnace provides warmth. It is not treated as a smelter or attached to a food line. Manual, helper-assisted and automated phases retain visible pickup, transport, processing and delivery.

## Storage upgrade: four explicit ports

| Interface | Location and transfer | Kept clear |
| --- | --- | --- |
| Utility IN | Low on the left wall; bounded receiving landing and indexed local tray/lift selects timber or mineral bay. | Original high left window and side service approach. |
| Utility OUT | Separate low left-wall dispatch landing; releases one permitted class against demand. | No automatic return to utility IN. |
| Prepared-food IN | Rear wall at prepared-food shelf height; short local horizontal tray/shuttle. | Closed raw-food cabinets below and round vent above. |
| Prepared-food OUT | Separate rear dispatch sleeve, with its own request-controlled outward line. | No automatic return to food IN; no raw-food feed into this line. |

Original front sliding doors, front apron and right fuel hatch remain identifiable and accessible. The new docks add footprint; the camp allocation reserves a continuous service approach around them.

**Clarification of the retained planning record:** the early R06/checkpoint phrase “low product sleeves” applies to the utility docks only. The final rear food docks sit at the prepared-food shelf, above the closed raw-food cabinets and below the original vent. The reviewed D03 art and D07 specification govern that clarified height. Historical requirement/checkpoint bytes are retained unchanged for provenance.

## Rules that make the system coherent

- **Typed release:** check the item family and allowed product before a carrier leaves its source.
- **Finite holding:** receiving trays, output buffers and reject pads have bounded capacity. Illustrative tray counts are not final balance values.
- **Destination reservation:** acquire a real free slot before transfer.
- **Full means wait:** a visible stop gate holds the next carrier; the wait propagates upstream instead of deleting goods.
- **Wrong item stays recoverable:** retain it at the source or a bounded reject pad. A full reject pad stops intake.
- **One transfer owner:** each carrier has one source/destination reservation and is consumed or handed over once.
- **Separate controls:** filtering chooses compatible goods; a diverter chooses one destination; a merge arbitrates arrivals. They are not interchangeable.
- **No storage circulation:** there is no automatic directed path from storage OUT back into its own IN.
- **Clear human access:** belts do not cross either primary gate corridor or the original storage entrance. The warming furnace, staff side and machine service faces remain reachable.

The catalogue checks validate IDs, ports, types and graph structure. They are not an inventory-engine simulation, mesh collision test or runtime pathfinding certification.

## What the existing references actually show

The audit inventories **all 23 registered video identities** and the **six registered stills**. Available evidence was visually inspected at these declared levels:

| Material | Inspection |
| --- | --- |
| Two owner-original MP4s | Verified file hashes; 64 decoded timeline samples, normally at two-second intervals. |
| Eight supplemental MP4s | Verified file hashes; 138 decoded timeline samples, normally at four-second intervals. |
| Original A late assembly sequence | 11 additional samples from 56.0–59.0 seconds, denser around the actual handoff. |
| Thirteen YouTube sources | All 122 archived storyboard sheets inspected. Full streams were unavailable. |
| Six registered stills | Actual images inspected. |
| Five immutable source documents | Retrieved against the baseline commit and matched to their Git blob hashes. |

This is a declared visual-sampling audit, **not a claim of end-to-end playback or audio review**. The original screen recordings include advertisements; advertisement edits are not proof of gameplay state transitions. The eight supplemental MP4s came through a third-party ad collection, not an official gameplay publisher. Storyboards cannot verify continuous motion or numerical throughput.

| Evidence window | Observed connection | Design consequence |
| --- | --- | --- |
| A, 14–16s | Whole-fish intake → incline → grill → cooked whole-fish output tray. | Distinct raw feed, processing and output buffer; no invented fillet stage. |
| A, 38–42s | Wheat-like belt feed → blue processor → round bread-like output. | Separate intermediate chain; exact recipe is unproven. |
| A, 56.5–59s | Two differentiated feeds → burger-marked assembler → short belt → vehicle counter; cash separately returned. | Explicit machine-to-machine and machine-to-counter links, with separate ingredient ports. |
| A, 18–56s | Player/helpers carry stock to pedestrian counters. | Carrying and automation coexist; staff approaches remain necessary. |
| B, 8–12s and 22–28s | Raw-looking logs and meat sold at matching counters. | Counter catalogue controls eligibility. |
| WS-S04, 20–28s | Intake → dedicated fish stock pad → manual vehicle loading. | A buffer is supported; an automatic universal warehouse is not. |
| WS-S08, 24–52s | Perimeter defensive resupply and a separate equipment line. | Reserve a future typed extension without inventing ammunition or crafting recipes. |
| YT07, storyboard only | Perimeter processing-to-counter path leaves the center open. | Spatial precedent only. |
| YT09, storyboard only | Lower resource yard → vertical hoist → upper camp. | Height-transfer precedent without a claimed cycle time. |

See [existing-reference coverage](research/existing/coverage.md), the [public source index](research/existing/public-source-index.json), [source observations](research/existing/public-video-observations.json) and the two attributed excerpt sheets listed in their positive archive manifest.

## Additional primary-source videos and evidence

Five actual developer clips from three official Wube/Factorio articles were downloaded, decoded and inspected as full-duration frame samples. Four were sampled at one frame per second; the rotation defect example at two. They are five clips from one publisher, not five independent sources. No continuous-playback or independent throughput-measurement claim is made.

| Primary source | Actual evidence inspected | Application to Havenline |
| --- | --- | --- |
| [Factorio Friday Facts #287](https://www.factorio.com/blog/post/fff-287) — [timing-gap clip](https://cdn.factorio.com/assets/img/blog/fff-287-splitter-gap.mp4) and [corrected clip](https://cdn.factorio.com/assets/img/blog/fff-287-splitter-no-gap.mp4) | Both 28.83-second timelines sampled; selected native detail. The developer describes a short input holding region resolving junction timing. | Give transfer junctions a bounded holding position; do not import another game's exact dimensions or rates. |
| [Factorio Friday Facts #442](https://factorio.com/blog/post/fff-442) — [drop-lane clip](https://cdn.factorio.com/assets/blog-sync/fff-442-inserter-drop-lane.mp4) | 18.12-second timeline sampled; markers change during selection/flip around 8–15s. | Make ports and destinations readable after placement or rotation. |
| [Factorio Friday Facts #442](https://factorio.com/blog/post/fff-442) — [rotation defect clip](https://cdn.factorio.com/assets/blog-sync/fff-442-em-plant-rotation.mp4) | 9.03-second timeline sampled; rotated connectors demonstrate an unwanted compatibility condition. | Revalidate direction and type after rotation or upgrade. This is a negative example, not desired mixing. |
| [Factorio Friday Facts #443](https://www.factorio.com/blog/post/fff-443) — [unloading clip](https://cdn.factorio.com/assets/blog-sync/fff-443-unloader-big.mp4) | 39.67-second timeline sampled; receiving structures and distinct outgoing transfer interfaces. | Separate inventory from physical receiving/dispatch adapters, scaled down for the camp. |
| [Factorio Friday Facts #225](https://www.factorio.com/blog/post/fff-225) | Primary developer documentation distinguishes input priority, output priority and filtering. | Define merge priority, routing priority and compatibility separately. |
| [Dorner Conveyor Transfers](https://www.dornerconveyors.com/blog/conveyor-transfers-video) — [video link](https://www.youtube.com/watch?v=mNLTL6utJMY) | Official page/title/description verified; the video stream was unavailable. | Physical analogy for aligned surfaces, side transfers and supported corners; not a watched-video claim. |
| [Dorner Lift Gates](https://www.dornerconveyors.com/blog/lift-gates) — [video link](https://www.youtube.com/watch?v=pxoI3sYpfxo) | Manufacturer documentation verified; embedded video unavailable. | Preserve walking access. This camp avoids crossing the two main gate routes. |

Additional source leads and their limits are preserved in the [new source register](research/new/new-source-register.json). The accumulation/elevator and SayGames trailer candidates were not visually inspected; they are not used as observed proof of Havenline behavior. The latter is not evidence for the chosen counter/cash layout.

## Verification and archive

The selected render studies are reviewed on their actual native pixels, including opposing views, closeups and normal/full or missing-input states where relevant. A separate visual critic reviews design and art; a separate archive critic checks the frozen package and publication integrity. Reviews bind exact file hashes. Rejected candidates and failed tool invocations remain recoverable rather than silently disappearing.

The archive is additive on a dedicated art branch based on commit `e3c787a4ecfffa7ae2013227d2db553f2e2829ef`. The baseline's 4,618 existing files are preserved. New content is confined to this conveyor-reference package. No runtime code, main branch or operational workflow is changed.

Original image outputs are retained byte-for-byte. Exact invoked prompt strings are distinguished from human-readable prompt documents that end with a newline. Actual supplied image inputs are ordered and hashed; an inspected source mentioned in a prompt is not falsely listed as an image input. The failed seven-reference camp invocation produced no image and remains marked accordingly.

Only explicitly selected research notes, registries and limited attributed evidence excerpts are included. Full third-party videos, full HTML and complete storyboard/timeline collections are not republished. Source URLs and verified identities allow the research to be resumed.

## Practical limits

This package establishes a coherent proposed transport family and readable static connections. It does not claim rigged/animated conveyor assets, meshes, exact world dimensions, collision clearance, pathfinding, final recipes, production costs or tuned throughput. Those require the game implementation and its own tests. The final acceptance/publication receipts state exactly which scope passed and which evidence was read back from GitHub.

