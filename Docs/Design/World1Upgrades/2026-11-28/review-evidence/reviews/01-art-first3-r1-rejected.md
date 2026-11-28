# Independent art review — first three r1 boards

**Result: 0/3 pass.** This is a review of actual static authored proposals, not owner design signoff or gameplay/model/animation approval. All known mandatory defects require repair.

## generated/01-counter-r1.png

**REPAIR_REQUIRED — 8.8/10.** File SHA-256 `4076f8745a8368cd21a0ce22b2996b68fce342917e858302b8ad79ecc0373488`.

- **W1AR-01 · Both rows, front versus rear food trays:** The tall divider at each tray’s physical left end in the front view becomes a broad short near-edge wall in the rear view instead of rotating to the corresponding screen-right end. The tray/divider topology is not consistent. Repair: Use the selected shallow tray design consistently, or show each divider at its correct rotated position. Keep cash and goods on the existing opposite physical ends.
- **W1AR-DOC · Generated stage labels versus UPGRADE_RENDER_BRIEFS.json:** Actual generator prompts and images name stages REINFORCED and ADVANCED; the separately authored inventory briefs give longer stage names and differing wording. Repair: Record a final deliberate mapping or update the briefs/manifest to the actual selected authored stage names. Do not label an unreviewed image as a different named stage.

Positive inspected findings: No register, till, cashier or new payment terminal visible. Both stages retain the timber table identity; advanced blue underframe is a readable proposed material change. Cash/goods ends reverse on screen appropriately between front and rear. Three panels per row are present, with close corner/material detail. Advanced front/rear bottom treatments can intentionally differ; their distinction must be recorded.

## generated/02-cooker-r1.png

**REPAIR_REQUIRED — 4.0/10.** File SHA-256 `2280dfe5a77bc9309c94a0cb51d023b5c4f3b8ecc3a457f149ce3218878dc08b`.

- **W1AR-02 · Top middle and bottom middle rear panels:** Rear service faces are shown, but raw remains screen-left and cooked remains screen-right just as in the front views. This swaps the machine’s physical input and output. Rear output containers also change from metal trays to timber boxes. Repair: Render the actual back: cooked output screen-left, raw input screen-right, with the same side vessel, pipe, tray materials and physical attachment positions as the front.
- **W1AR-03 · Third column, both rows:** The panel called FUNCTIONAL SIDE is a straight front view of the same firebox and both side trays. It does not establish a distinct functional-side/detail relationship. Repair: Provide a genuine functional-side detail, correctly oriented to the same model, showing the handoff/chamber/service relationship without moving ports.
- **W1AR-DOC · Brief labels:** Generated Reinforced/Advanced names differ from inventory brief stage names. Repair: Align selected-image manifest and briefs after visual repairs.

Positive inspected findings: Both rows remain recognizable cooker-family concepts with one centered chimney and a front firebox. Material style, proposed reinforcement, snow treatment and broad stage readability are coherent. No levels, costs, new recipes or runtime claim are printed.

## generated/03-saw-r1.png

**REPAIR_REQUIRED — 4.0/10.** File SHA-256 `c5b4619b05f26cf998e5cb746c8d6da273d4f6e34757222064151d3b97c838f5`.

- **W1AR-04 · Middle column, both rows:** The purported REAR THREE-QUARTER panels still put the visible blade face and crank in front of the log. They are additional front views. Actual rear/clamp coverage is missing. Repair: Use a true opposite rear view: log/clamp foreground and cutter/crank on the correct far side, consistent with the selected baseline.
- **W1AR-05 · Right side-detail column, both rows:** An edge-on vertical blade strip appears beside a broad semicircular toothed form facing the side camera. The cutting head is drawn as two incompatible perpendicular forms rather than one coherent disk/guard. Repair: Keep one blade disk and its guard on one plane, with a single consistent crank axis. Side view should show the correctly edge-on assembly and clearance to the log.
- **W1AR-DOC · Brief labels:** Generated Reinforced/Advanced names differ from inventory brief stage names. Repair: Align selected-image manifest and briefs after visual repairs.

Positive inspected findings: Both rows preserve the compact timber saw table, upper clamp, log and under-table plank family. Blue reinforcement/guard changes are visibly distinct between rows. No new engine, fuel requirement or producer is asserted by text.

## Retest boundary

Use newly saved repaired images with new hashes. Do not overwrite rejected r1 images. Independently inspect actual repaired front/rear/detail views and reconcile stage names in the final inventory/manifest. Full raw scores, source hashes and candidate bindings are in the companion JSON.
