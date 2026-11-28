# World 1 appearance-upgrade render briefs

**Scope: 15 authored concept sheets, 30 proposed visual stages and 90 requested views.** These are not approved numerical equipment upgrades or World 1 unlock assignments. The user has settled ten worlds with fifty levels each; that does not mean fifty appearances per asset.

Existing furnace and storehouse forms are reused. Conveyor appearance is excluded; the selected conveyor/resource scale is fixed. No new character, survivor or pet appearance progression is invented.

| Brief | Family | Proposed stage A | Proposed stage B |
|---|---|---|---|
| W1UP-01 | Customer counter | REINFORCED | ADVANCED |
| W1UP-02 | Camp cooker processor | REINFORCED | ADVANCED |
| W1UP-03 | Saw station | REINFORCED | ADVANCED |
| W1UP-04 | Quarry drill station | Reinforced Quarry Station | Braced Quarry Station |
| W1UP-05 | Fish-line intake and automation | Reinforced Fish Intake | Sheltered Fish Intake |
| W1UP-06 | Stationary wheat harvester | Reinforced Field Harvester | Shielded Field Harvester |
| W1UP-07 | Wheat food processor | Reinforced Wheat Processor | Insulated Wheat Processor |
| W1UP-08 | Iron smelter | Reinforced Iron Smelter | Insulated Iron Smelter |
| W1UP-09 | Metalworking bench | Reinforced Forming Bench | Guided Forming Bench |
| W1UP-10 | Steel forge | Reinforced Steel Forge | Insulated Steel Forge |
| W1UP-11 | Assembly bench | Reinforced Assembly Bench | Braced Assembly Station |
| W1UP-12 | Manual oil pump | Reinforced Manual Pump | Weatherproof Manual Pump |
| W1UP-13 | Fuel refinery | Reinforced Fuel Refinery | Insulated Fuel Refinery |
| W1UP-14 | Snow truck garage | Reinforced Snow Garage | Insulated Snow Garage |
| W1UP-15 | Player snow truck | Reinforced Snow Truck | Winter-Armored Snow Truck |

Each stage receives front three-quarter, rear three-quarter and functional-side/detail views. New appearances must retain the baseline footprint, source-visible identity, port sides/heights, manual access and world-scale relationships.

## Source precedence

- The historical counter reference contributes table proportions only. Its register/staffing assumptions are superseded by current self-service sheets and owner rules.
- The selected manual pump uses the rendered hand crank, rocking beam, piston and buffer; older abstract lever prose does not replace it.
- Metalworking and assembly each remain one producer with two alternative recipes.
- Fish-line intake remains a support asset for the existing whole-fish cooker route; wheat retains its existing direct bread route.
- Truck/garage artwork does not bind unlock levels. Latest vehicle-economy rules retain low fuel use and an attainable manual first-fuel path.

Exact prompts, source images, hashes and invariants are in [UPGRADE_RENDER_BRIEFS.json](UPGRADE_RENDER_BRIEFS.json) and [UPGRADE_SOURCE_MANIFEST.json](UPGRADE_SOURCE_MANIFEST.json).

Generation, visual review, owner adoption, native models, animation, runtime integration and numeric upgrade registration remain separate evidence stages.

## Vehicle source precedence limits

Low fuel consumption is the current requirement. VC01 (partial versus whole-load garage deposit) and VC02 (general in-camp blade operation) remain unresolved in the shared World Progression contract. These static appearance briefs preserve garage access and the original blade geometry without choosing either disputed behavior. See `UPGRADE_SOURCE_MANIFEST.json` for the source crosswalk.

## Planning briefs and actual generation records

The JSON `prompt` and `ordered_inputs` fields are the planning brief and intended reference set. The actual per-iteration prompt records and candidate manifest determine the prompt, reference images and output identity used in each invocation. Do not infer that every planning input was supplied to every iteration.

The first three sheets use the displayed labels **REINFORCED** and **ADVANCED**. Their family-specific stage IDs and original authored concept names remain in JSON. The other twelve briefs retain their full named stages. The first counter, cooker and saw iterations are retained as rejected history pending fixes; none is selected by these inventory files.
