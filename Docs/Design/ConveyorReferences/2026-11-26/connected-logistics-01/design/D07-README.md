# D07 — exact route specification and camp allocation

## Files

- `D07-01-directed-routing.svg` / `.png`: food, optional two-input assembly, utility and manual-service routes.
- `D07-02-camp-allocation.svg` / `.png`: conceptual camp allocation with central heater, two clear bidirectional gates, separate storage cassettes and service space.
- `routing-catalogue.json`: 37 stations/dispositions, 25 directed routes and all 14 source equipment families.
- `D07-design-evidence-map.json`: decisions mapped to requirements and source evidence.
- `D07-builder-verification.json`: file hashes, pixel-review status, structural checks and retained-draft defects.
- `build_d07.py`: editable deterministic SVG/catalogue build script. Run with the available Python/Pillow and Inkscape environment.

## Reading the route specification

Solid colored arrows describe proposed directed transfers. The observed source forms/topology are identified in notes and the evidence map. Dashed equipment cards remain provisional until their exact recipe or catalogue is defined. Teal marks food, ochre utility materials and gray manual service. Each destination reserves a slot before release; full and wrong-item states retain goods and stop further intake.

Storage receiving and dispatch are separate local operations. Food dispatch cannot automatically return to food receiving; utility dispatch cannot return to utility receiving. The JSON graph validates those two conditions and validates every source/output and destination/input port. This is a structural specification check, not a simulation test.

The optional assembler requires separate bread-like and compatible cooked-input magazines; it is not a generic mixed-input merge. Its source topology is observed around A56.5–59s, but no exact ingredient identity, ratio, fuel, production time or Havenline machine recipe is frozen. The two-ingredient/output reservation applies when a cycle starts. Completed output is released against its own destination reservation, so dispatch does not depend on ingredients already consumed. Manual rod acquisition and mechanized intake are alternative phases; an optional manual loading port is a new proposal, not an observed serial feed.

## Reading the camp plan

The heater is centred in the camp allocation. Its pale ring is a warmth illustration. The original storage door/apron and the two primary gate paths remain free of belts. New rear prepared-food and left utility cassettes occupy visible footprint with local inventory interfaces and reserved service aisles. The rear food sleeves align with the prepared-food shelf above the closed raw-food cabinets, using a short horizontal tray/shuttle. The low utility cassette uses an indexed local tray/lift. The high window, rear vent and original right fuel hatch remain identified as retained features. The utility intake selects either timber or mineral trays, and its separate dispatch collects from the selected compartment. A continuous service spine connects the clear gate corridor with the left and rear service aisles. The food conveyor ends at a separate dead-end staff buffer; staff lift stock onto the original wooden counter. The customer queue and cash collection have separate areas.

No dimensions, runtime collision fit, pathfinding or final structural clearance are approved by the schematic. The optional assembly pad is reserved space; its detailed two-input connections are on D07.1. Raw-food storage, hides, cargo/cash and fuel are not claimed as automatically connected.

## Review state

Builder pixel inspection found and repaired text overflow, annotation/arrow overlap, gate-label occlusion and an overlarge heater drawing. The rejected first draft is retained in `revisions/draft-v1/`. Root and independent-critic review of the second draft identified reversed utility semantics, an ambiguous stock-to-table handoff and isolated service aisles. Those three findings are repaired in r3; the reviewed second draft is retained in `revisions/draft-v2/`. The third draft is retained in `revisions/draft-v3/`. R4 also corrects the manual-acquisition evidence classification and separates assembler cycle-start conditions from completed-output dispatch. The reviewed fourth draft is retained in `revisions/draft-v4/`. R5 synchronizes the prepared-food tray/shuttle and utility lift terminology with the updated storage design. The current previews and critical-area crops are recorded in the verification receipt. Current SVGs parse and PNG previews render correctly. Independent reviewer `/root/conveyor_critic` inspected the actual r5 SVG/PNG outputs and the catalogue, then recorded **PASS_SCOPED_DESIGN_ONLY, 9.8/10**, with all 14 scoped checks passed. The exact current output hashes are bound by `../reviews/d07-final-scoped-review.json`; its separate catalogue check confirms all 37 stations, 25 routes and 14 equipment families. This approves the design specification only; it does not approve runtime implementation, exact world scale, recipes or the complete render/archive package.

## Source archive selection

`../references/new/PUBLIC-ARCHIVE-MANIFEST.json` names the exact original notes/registries and three limited attributed source details selected for preservation. It excludes full third-party videos, full HTML, broad contact sheets and failed media responses. Current design files, critical-area review crops, and the retained design revisions are listed separately in `PUBLIC-DESIGN-ARCHIVE-MANIFEST.json`. This subtask performs no GitHub writes.
