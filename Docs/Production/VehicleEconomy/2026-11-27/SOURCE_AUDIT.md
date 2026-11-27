# Vehicle economy — source audit

Captured 2026-11-27T17:43:53.299250+00:00. This is a read-only source review. The APK, videos, sound and device evidence were not replayed. It does not certify the current game.

Package base `201dcbe4fad5037a33bd619b59285a1ef91599d8`. Live game `ea6e4896cc6692ee84b56f89e127feaa606eb370` is **Build14**, newer than the Build13 selector retained on main. Planning audit `5862b89c1663cacc0cbb84bfaba438d1459cfdb6` remains a separate concurrent source. Exact Git blobs, byte lengths, SHA-256 bindings and inspected excerpts are in [SOURCE_AUDIT.json](SOURCE_AUDIT.json).

## Verified source findings

- **S01:** Newest observed gameplay is Build14 and already contains a driveable truck, input routing, physical movement/contact code, docking, outside loss, inside salvage and fixed garage-time quote selection. These paths were inspected, not executed in this source audit.
- **S02:** Live raw IDs remain wood, stone, meat, coal, slate, metal; metal display is Metal ore. No live iron_bars, sheet_metal, crude_oil or fuel balance exists in the fixed10-item truck cargo catalogue.
- **S03:** One existing raw ledger count is a ten-unit physical bundle. One saw/quarry cycle consumes one bundle and produces one product count. Decimal migration must preserve that denomination.
- **S04:** Coal is a mined raw resource. Fuel was a distinct authored salvage resource; steel was an authored future processed output. No new metal/refinery chain is proven live by these sources.
- **S05:** T44–T52 themes map to Forest/Lakeshore, Desert/Canyons, Underwater, Sky, Volcanic, Swamp, Ruins, Underground and Alien Frontier. Dry habitat routes, fixed bridges/lifts, no people on conveyors and finite relay project identity constrain new vehicles.
- **S06:** Build14 QA reports scoped9.5–9.6 review scores and outstanding physical Galaxy Z Fold7 evidence and destruction coverage. This audit did not replay its APK, videos, audio or assertions and grants no new approval.

- **S07:** Build14 payment, repair, repurchase, transfer and restore still use fixed typed dictionaries/native integers. Its price formatter iterates eight IDs and scales all but planks/blocks by ten. New recipes need coupled exact custody and per-ID display adapters. Keep fractional tank estates outside ordinary-salvage repurchase gating, so buying a live replacement can happen before recovering estate fuel.

## Conflicts and current disposition

| Conflict | Disposition |
|---|---|
| Audit and Build14 stop blades when touching camp; prior published selected feature permits deliberate eligible-hostile defense with safe default travel. | Keep defense as selected integration requirement. Stop tools for docking/refuel/service, prohibit incidental friendly/owned-structure damage. Existing source gap stays explicit. |
| Concurrent progression prose permits partial unload/full-store waiting; published feature requires automatic entire load transfer to all-resource unbounded warehouse, otherwise whole-load HOLD. | Retain all-or-hold automatic transfer and any-resource unlimited cargo. Fixed live cargo IDs and world receiver binding need migration/integration. |
| Prior package introduced no fuel and concurrent audit leaves fuel open. | Latest owner expansion explicitly selects low fuel consumption; this new version adds a funded tank and free-of-fuel bootstrap, without editing old frozen package or old payment obligations. |
| Older authored steel route directly consumes ore+coal; owner now requests iron ore to bars to sheet. | Add bars and sheet chain; keep steel as purposeful advanced bar+coal branch. Preserve original recipe versions for in-flight/owned state. |
| World progression local50/500-level proposal and older100-outcome contract are not yet reconciled. | Use authentic region/task identity and capability-gated vehicles; commit no new level cap or numerical unlock. T71–T80 remain undefined. |
| Finite relay_component is identified as a project object but the source does not establish portable versus structural classification. | Forward authored choice: a portable serialized module follows outside cargo loss and can be replaced at its restored worksite for an attainable ordinary-material bill, with the same objective serial, one active instance and one-install tombstone. Exact replacement bill remains pending; preserve existing save identity through explicit migration. The earlier fixed-site nonportable alternative is superseded and retained in SOURCE_AUDIT.json. |

## Custody and next action

Pinned files were read with `git show` at the named commits. The U3/resource source files are separate read-only worktree bytes, identified by their own hashes; their surrounding worktree HEAD is not asserted to contain those bytes. No old worktree, branch or freeze was changed. The normalized owner expansion in RESOURCE_CHAINS is a task relay, not a fabricated verbatim quote.

The gameplay owner should reconcile the current live head before integrating the new catalogue, recipe and fuel adapters. Preserve existing saved bills, raw denominations, vehicle ownership and all prior evidence. Review the existing truck behavior against current owner requirements and source-bound mandatory gates; do not upgrade scoped9.5–9.6 or unplayed media into final acceptance.
