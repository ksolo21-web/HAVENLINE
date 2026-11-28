# Complete conveyor render coverage

**36 required coverage cells in 9 study groups.** These are module/interface obligations, not a fixed image count. The previous seven studies establish historical scope; their old approvals do not approve the revised set. The selected R1 fishing line is a baseline, not a substitute for every module.

## Current authority

- Keep the owner-selected R1 orange/yellow, dark-roller, gray-plate and blue-base family and its selected size. Keep Character1 fixed and use core R4 for ordinary pickups.
- Fish types and animal-dependent meat cuts may differ in size; a given physical item keeps its size across every handoff.
- The current counter is register-free and self-service. The historical staffed/register rendering is superseded.
- This matrix is for static render coverage. Motion and integration remain unapproved.

## Required catalogue

### G01 — Transport modules

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| T01 | **Level straight**. Low supported dark-roller carrying surface, approved R1 orange/yellow frame and blue base/drive treatment; visible matched ends. | existing static render — D01 | opposing three-quarter views; largest intended load resting on rollers; same fixed C1 anchor |
| T02 | **90-degree left corner**. Continuous supported roller arc with a readable leftward transfer direction and unbroken inner/outer support. | existing corner family render — D01 | top-oblique; entry/exit connection close-up; largest-item swept clearance |
| T03 | **90-degree right corner**. Right-turn placement or handed module of the same kit; do not assume a single isolated left turn proves both placements. | existing corner family render — D01 | top-oblique; entry/exit connection close-up; largest-item swept clearance |
| T04 | **Rising height adapter**. Supported rise with restrained/cleated carrying surface where necessary, smooth low and high transfer plates, fixed item size. | existing static render — D01 | side profile; loaded rising arrangement; both endpoint heights |
| T05 | **Falling height adapter**. Descending use of the kit with contained loads and a supported lower landing; visible direction differs from the rise. | existing height adapter family — D01 | side profile; loaded descending arrangement; receiving stop/landing |
| T06 | **End coupler and bridge plate**. Gray supported bridge plate and mating frame ends maintain the R1 intake/roller/plate relationship; no open unsupported transfer gap. | existing static render — D01, D04 | joined close-up; side support view |

### G02 — Routing, buffering and crossings

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| R01 | **One-input/two-output diverter**. One incoming stream, two exclusive compatible outgoing branches, visible selector; distinguish route choice from item filtering. | existing static render — D02, D07 food-router | both branch selections; blocked branch state |
| R02 | **Two-input/one-output gated merge**. Separate gated approaches share one reserved outgoing slot; show one held while the other releases. | existing static render — D02, D07 food-merge | opposing views; alternating grant/hold states |
| R03 | **Finite stock/output buffer and stop gate**. A bounded receiving surface with visible end restraint and input stop; loaded/full state preserves every item. | existing static render — D02, D04, D05 | ready with free space; full with intake paused; pickup access |
| R04 | **Wrong-item hold / bounded reject landing**. Show a physical upstream stop gate and the selected compatible type. A wrong family is held BEFORE the incompatible interface or on a connected bounded reject landing; an unrelated wrong item lying nearby is insufficient. | existing static render — D02, D07 global rules | compatible flow; wrong item held outside incompatible line |
| R05 | **Grade-separated conveyor crossing**. Two independent routes cross at separate heights with supported approaches and visible vertical item clearance; no opaque overlapping cargo. | code authored no dedicated archived study — Build14 field_conveyor_crossings.gd | top-oblique showing both paths; side clearance view; largest loads on both paths |

### G03 — Storage IN/OUT and local transfers

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| S01 | **Utility storage IN**. Low left-wall receiving cassette below the retained window; class-selectable timber/mineral tray with inward direction. | existing static render — D03, D07 utility-storage-in | left exterior; receiving full/held state |
| S02 | **Utility storage OUT**. Separate low left-wall dispatch cassette; releases requested compatible stock without a path back to its own IN. | existing static render — D03, D07 utility-storage-out | left exterior; selected outgoing class |
| S03 | **Prepared-food storage IN**. Rear receiving cassette at prepared-food shelf height, above closed raw-food cabinets and below the retained vent. | existing static render — D03, D07 food-storage-in | rear exterior; loaded inward transfer |
| S04 | **Prepared-food storage OUT**. Separate rear request-controlled dispatch sleeve at shelf height; no automatic OUT-to-IN circulation. | existing static render — D03, D07 food-storage-out | rear exterior; loaded outward transfer |
| S05 | **Local utility indexed tray/lift**. Visible local transfer between the left cassettes and selected timber/mineral bays; no invisible tunnel through house. | existing static render — D03, D07 utility-inventory | interior cutaway; class-selected tray position |
| S06 | **Local prepared-food tray/shuttle**. Short horizontal shelf-height transfer between rear food cassettes and prepared-food stock. | existing static render — D03, D07 food-inventory | interior cutaway; separate IN/OUT physical paths |

### G04 — Raw and prepared-food machine docks

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| F01 | **Shore intake and front discharge**. Retain selected R1 intake silhouette, dark rollers, gray plate, blue base and larger-fish context without resizing the chosen line. | existing static render and selected r1 baseline — D04, selected conveyor R1, original A sampled playback | front discharge close-up; opposite angle; same largest fish fit |
| F02 | **Cooker raw-food input dock**. Supported adapter reaches physical-left raw input with real matching height/width and clear front controls. | existing static render and selected r1 baseline — D04, D07 cooker.raw-in | raw approach and port close-up; opposing angle |
| F03 | **Cooker processed-food output dock**. Physical-right output reaches a finite supported buffer; output preserves the cooked species presentation family. | existing static render and selected r1 baseline — D04, D07 cooker.cooked-out | output close-up; full buffer with cycle held |
| F04 | **Meat-to-meal dock use**. Show current smaller ordinary Stag/wolf meat at typed raw input and species-aware cooked meal at output using selected cooker geometry. | authored route no separate legacy dock study — current RESOURCE_MACHINE_MAP meat/meal, existing camp_cooker | loaded raw and cooked interfaces; clear controls and carry approach |
| F05 | **Wheat processor raw and bread output docks**. Show wheat arriving from the harvester/source output into the selected processor and bread leaving through its distinct supported output. | authored existing machine no separate legacy dock study — D07 wheat-harvester/wheat-processor, current wheat_food_processor | connected input/output overview; each transfer close-up |

### G05 — Timber and mineral machine docks

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| U01 | **Typed raw utility feeder**. Separate timber/mineral staging and selected release onto utility transport; logs, stone and ore retain their existing forms. | specified in d07 not separate legacy render — D07 utility-feeder, R-U00, R-U02, R-U03 | timber selected; mineral selected; wrong class held |
| U02 | **Saw wood input and plank output docks**. Visible wood receiving support and separate plank discharge adapter; preserve selected saw identity and operating reach. | existing machine authored route dock render required — current saw_bench, D07 saw-variant | connected overview; loaded inlet/outlet close-ups |
| U03 | **Quarry/stone processor input and block output docks**. Distinct raw-stone feed and finished-block discharge supports with preserved quarry/processor identity. | existing machine authored route dock render required — current quarry_drill, current stone/blocks route, D07 quarry | connected overview; loaded inlet/outlet close-ups |

### G06 — Industrial machine and container interfaces

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| I01 | **Coal smelter typed interfaces**. Separate metal ore chute and low coal drawer, opposite iron-bar cooling/output tray, plus clear manual control apron. | selected machine sheet new connected dock study required — PROCESSING_MACHINE_MAP coal_smelter | ore/coal approach; bar discharge; full output hold |
| I02 | **Metal bench input and alternative outputs**. One iron-bar feed rack; separate sheet tray and parts bin; show the selected recipe output and accessible handwheel. | selected machine sheet new connected dock study required — PROCESSING_MACHINE_MAP hand_metal_bench | sheet mode connected; parts mode connected; same inbound interface |
| I03 | **Steel forge typed interfaces**. Iron-bar cradle, separate coal hopper and steel cooling/output rack; match selected squat forge silhouette. | selected machine sheet new connected dock study required — PROCESSING_MACHINE_MAP steel_forge | two input approaches; steel discharge; front apron |
| I04 | **Industrial assembly multiple-input docks**. Three separated inbound staging positions: steel, mechanical parts, and recipe-specific sheet metal OR planks; broad assembly output cradle. | selected machine sheet new connected dock study required — PROCESSING_MACHINE_MAP assembly_bench | drive job with all three inputs; mobility job with all three inputs; largest output cradle and clear hoist control |
| I05 | **Manual pump crude container handoff**. Preserve sealed crude coupling, detachable collection drum pickup and walking return access; show compatible receiving/staging handoff. | selected machine sheet manual interface — PROCESSING_MACHINE_MAP manual_oil_pump | sealed collection outlet; full/held container and manual pickup access |
| I06 | **Refinery crude/coal inputs and fuel output**. Sealed crude-drum coupling, separate coal drawer and distinct clean-fuel can cradle; show finite staging/transfer and manual access. | selected machine sheet new connected dock study required — PROCESSING_MACHINE_MAP coal_refinery | separate typed inputs; fuel output and collection; output full/held |

### G07 — Reserved dual-input food assembly

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| A01 | **Reserved two-input food assembler**. Separate ingredient A/B magazine interfaces and one supported product output in current kit style; show input-wait and output-full states. | existing static concept recipe unfrozen — D04B, D07 optional-assembler | two input approaches plus output; missing input; output full |

### G08 — Self-service counter connections

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| C01 | **Self-service food counter restock and separate cash**. Supported restock/stock surface with finite full-stop, accessible customer face, player/helper bulk visit position and separate cash pickup area; no register or random clerk. | historical counter render superseded — D05 buffer topology only, Nov27 bulk/self-service override, Build14 field_counter.gd, field_goods_exchange.gd | customer-facing overview; rear/side loading and cash separation; normal and stock-full states |
| C02 | **Catalogue-gated material counter dock use**. Show compatible selected material stock entering its own allowed counter area with no food/fuel mixing and separate cash. | specified d07 current counter override applies — D07 material-counter, Build14 current market catalogue | allowed material stocked; ineligible form held |

### G09 — Connected camp and expanded routing

| ID | Required visible module/interface | Existing evidence | Required views/states |
| --- | --- | --- | --- |
| N01 | **First connected camp route**. Readable intake→cooker→prepared-food IN/local stock/OUT→self-service counter route; centered warmth heater, two clear bidirectional gates and protected house access. | existing static render needs current counter style — D06, D06 initial deployment, selected conveyor R1 | complete oblique route overview; opposing/raised view exposing rear and left ports; service/carry approaches |
| N02 | **Expanded compatible machine-to-storage/counter network**. Show food, timber/mineral and industrial paths as separate typed lanes with usable branch/merge/height interfaces, protected worker aisles and compatible destination docks. | d07 authored plan plus current machine expansion — D07, current RESOURCE_MACHINE_MAP, PROCESSING_MACHINE_MAP | readable connected overview; second view or focused industrial connection inset; clear route/direction labels |

## Boundaries that must survive rendering

- Storage utility IN/OUT sit low on the left below the window. Prepared-food IN/OUT sit on the rear at shelf height, above raw-food cabinets and below the vent. Preserve the front door/apron, center aisle, right fuel hatch and service approaches.
- The historical two-input food assembler is a reserved interface concept. No burger wallet, recipe, quantity or sales menu is introduced. The later industrial assembly bench is a different selected machine with three staged recipe inputs.
- The manual oil pump needs sealed collection and pickup coverage. It does not authorize open liquid on a belt, a new camp pipeline, empty-drum inventory or fuel-powered bootstrap. Refinery container interfaces do not silently automate the historical manual fuel hatch.
- Current wood→planks, stone→blocks and the six selected industrial machines supersede older historical claims that those routes/equipment were unfrozen or unassigned. Historical art is preserved; current recipe identities control.
- Separate typed food, material and industrial paths. Cash, Gems, cargo wrappers and finite relay objects do not gain production belts merely because they have renders.
- Crossings need supported clearance for the largest accepted items and a separate side view. Human gate corridors remain clear. Old numeric code dimensions are audit facts, not new art scale targets.

## Closure rule

The builder records each new image and reviewer record against the individual IDs in the JSON. A study closes only when every mapped geometry, interface and required use state is actually visible, all mandatory checks pass, and a separate critic satisfies the current reference policy: exact unrounded 10 for applicable reference/style critics, at least 9.9 for additional reference-sensitive dimensions and at least 9.5 otherwise. All mandatory checks must pass; no averages or missing evidence can close a cell. Alternate views of the fishing line cover only the cells they visibly show. A static concept cannot close runtime motion, physics or stock conservation.

## Provenance

All seven images in `source/previous-conveyors/` were visually inspected and their bytes matched the archived generation manifest. The archive records content commit `e501bea5ed9e6f8737abb5b39799cade78b22af1` and final receipt commit `d70fbfac21a852f99cc46b06b1944faf11ec7901` on `art/conveyors-2026-11-26`. This is a local archived-record binding, not a fresh remote branch-head assertion. Exact source file hashes and all per-cell boundaries are in the JSON.

No source art, original videos, previous approvals, gameplay or remote files were modified by this matrix build.
