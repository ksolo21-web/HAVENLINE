# Havenline — resources and complete conveyor render set

[Open the selected render gallery](GALLERY.md)

## November 28 continuation

The selected delivery contains **26 full-size sheets** plus a four-view PDF. All **36 static conveyor coverage cells** passed their required independent reviews. The resource set retains **27 canonical families**, **four fish types with eight raw/cooked depictions**, and **ten animal-specific meat studies**. The two owner-selected size baselines remain byte-identical.

This continuation repaired the shore conveyor's left-side roller consistency and the expanded network's true storage and cassette openings. The four-view PDF preserves the exact reviewed front, rear and right image panels and uses the independently corrected left panel. Its exported page and its source map are included in `presentation/`.

The final coverage record distinguishes the 34 prior approvals carried by verified unchanged hashes from the two freshly reviewed repairs. It is a completed static reference delivery; native assets, motion, actual size in the game, collision and inventory behavior still need their own implementation and evidence.

This revision follows the owner's final size selection: the original conveyor line R1 and the compact core-resource sheet R4. Those two selected files are unchanged. The later request expands the deliverable to the whole conveyor catalogue, including processing, storage and counter connections.

## What is included

The selected gallery contains the approved resource-size comparisons, fish and animal-meat variations, conveyor modules, routing and hold states, processing-machine interfaces, storage transfers, self-service counters, and connected route studies. The exact selected-file count and the independent status of every one of the 36 conveyor coverage cells are recorded in [the selected manifest](SELECTED_ASSET_MANIFEST.json) and [the coverage checkpoint](STATIC_COVERAGE_CHECKPOINT.json).

The module catalogue covers level straight runs, left/right corners, rising and descending adapters, joined bridge plates, diverters, gated merges, finite buffers, incompatible-item holds and grade-separated crossings. Machine studies cover the cooker, wheat processor, saw, proposed parked quarry cassette, smelter, metal bench, steel forge, assembly bench, manual oil pump and refinery. The historical two-input food assembler remains a reserved interface concept.

Storage retains separate utility IN/OUT and prepared-food IN/OUT, local receiving and dispatch mechanisms, and clear building access. Counter studies retain autonomous self-service, visiting-player/helper bulk loading and collection, accessible stock and separate cash. The connected camp uses the current meat-to-meal example; expanded studies trace typed utility and industrial routes.

## Size and resource continuity

All 27 existing resource/item identities are retained. Character1's identity and reference stature stay fixed. Ordinary units follow the approved compact reference. A larger stockpile consists of more units; an individual unit does not change size at a belt, dock, shelf or counter.

Four fish presentation studies show small common fish, small perch, medium trout and large salmon, each in raw and cooked form. Ten animal-meat studies preserve the historical distinct cuts. These are visual variants inside the existing resource families, not new wallets, recipes, unlocks, animal spawns or drop balances.

See [the variant contract](integration/RESOURCE_VARIANT_CONTRACT.json) and [the function handoff](integration/CONVEYOR_FUNCTION_CONTRACT.md).

## Review and implementation boundary

The independent reviews inspect the actual generated images, multiple views, closeups and the displayed normal/full/held states. An approval applies only to the image and scope identified by its hash and report. The selected set excludes rejected and superseded attempts; those remain archived with their prompts and findings.

Static render acceptance does not prove a working native asset, animated conveyor cycle, collision clearance, navigation, processing execution, inventory conservation or cash accounting. The source-playback ledger records only the original video intervals actually inspected. A new in-engine candidate still needs its own full-cycle evidence and tests before anyone can claim a 100% functional match.

The parked quarry processing cassette is an authored connection proposal, not a recovered source-video feature. Assembly input conveyors end at explicit manual loading trays. The oil pump keeps manual sealed-container pickup. Current active market examples remain meal, planks and blocks; other rendered items do not gain sales eligibility from appearing in art.

## Package structure

- `selected/`: unchanged native PNGs selected by exact owner approval or independent static review.
- `attempts/`: preserved candidates, including rejected and superseded iterations.
- `prompts/`, `requests/`, `receipts/`: generation and custody records.
- `reviews/` and `evidence/`: independent findings and actual-image inspection evidence.
- `plan/` and `integration/`: requirements, source audit, coverage, variant/processing contracts and resumption notes.
- `tools/build_selected_gallery.py`: reproducible selected-only gallery and manifest builder.

This package is confined to the isolated art branch. The earlier completed resource and machine-turnaround packages are retained by the parent commit. It does not modify gameplay scripts, scenes, project settings, workflows or the default branch.

