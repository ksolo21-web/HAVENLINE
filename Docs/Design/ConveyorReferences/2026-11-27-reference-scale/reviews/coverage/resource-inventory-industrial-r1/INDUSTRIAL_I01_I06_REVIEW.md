# Independent industrial conveyor review — I01–I06

**HOLD — 7.5/10.** Neither candidate passes the static connection scope yet. Mandatory source identity, handoff and hold-state evidence is missing or inconsistent. This is a separate actual-pixel review by `/root/resource_inventory`; the reviewer did not create or edit either root-built candidate.

## What works

All six canonical machines remain recognizable. The approved orange/yellow closed conveyor family, dark transverse rollers, silver plates and blue bases are consistent. The sheets keep the two metal-bench modes and the drive/mobility jobs separate. Crude and clean-fuel containers are distinguishable, and the pump explicitly retains manual pickup.

## Mandatory checks

| Matrix | Score | Status | Concrete repair |
|---|---:|---|---|
| I01 | 7.8 | HOLD | correct outgoing iron identity; mandatory full-output-held view |
| I02 | 8.0 | HOLD | canonical iron-bar stock; sheet-mode inactive parts tray empty |
| I03 | 7.8 | HOLD | canonical iron-bar input; physically clear coal-hopper join |
| I04 | 7.2 | HOLD | canonical mobility identity; clear receiving/staging handoffs; compact selected output scale evidence |
| I05 | 8.7 | HOLD | detachable crude-unit selected size match |
| I06 | 8.1 | HOLD | physical terminal restraint for full/held output; detachable crude-unit selected size match |

## Consolidated repair list

### IND-R1-01 — I01, I02, I03

Iron resource identity is inconsistent. The smelter cooling tray holds dark rectangular bars, while the adjoining belt changes them into short bright trapezoidal ingots. All IRON-labelled infeed belts repeat the bright ingot form. Selected04 iron_bars is the dark elongated rectangular bar; steel is the separate blue trapezoidal ingot.

**Repair:** Use unchanged selected iron_bars silhouette/color at every iron input/output and on the smelter cooling tray. Preserve blue steel ingots only for steel. Do not change recipes.

Evidence: [15a-smelter-iron-identity](evidence/15a-smelter-iron-identity.png), [locked-iron-identity](evidence/locked-iron-identity.png).

### IND-R1-02 — I01

No smelter full-output held state is present. The only smelter panel shows ordinary input/output stock, so the mandatory full-output behavior cannot be inferred.

**Repair:** Add an explicit smelter full-output view: cooling/output capacity visibly occupied, restrained discharge, feed approaches held and manual control apron clear. Retain the successful normal ore/coal/discharge view; a separate additional view is preferable to compressing an unreadable fifth panel.

### IND-R1-03 — I02

SHEETS mode retains a loose gear and bracket in the parts output tray under the press. Together with discharged sheets, it reads as both recipes producing concurrently. The source props are not exempt from the one-selected-output requirement.

**Repair:** Empty loose contents from the inactive parts output tray in SHEETS mode; retain the permanent press/dies/housing. PARTS mode may keep its parts output and empty sheet chute. Use the same iron input in both.

Evidence: [15a-sheet-inactive-parts](evidence/15a-sheet-inactive-parts.png).

### IND-R1-04 — I03

The forge coal conveyor ends against the stone foundation beneath the iron-bar cradle; the supplied image does not reveal a separate coal receiving opening/hopper at that join. A label naming COAL does not establish a typed physical handoff.

**Repair:** Route the coal approach to the forge's real separate coal hopper with a visible supported height transition and open receiving throat. Keep the iron-bar cradle and steel cooling rack separate; show another angle/inset if the rear hopper would otherwise remain hidden.

Evidence: [15a-forge-coal-interface](evidence/15a-forge-coal-interface.png).

### IND-R1-05 — I04

MOBILITY ASSEMBLY is a black caterpillar track with orange wheels. Selected05 mobility/traction_kit is a compact blue/orange axle-like assembly on a small wooden base. The candidate introduces an incompatible rubber/track identity.

**Repair:** Replace only the output with the exact selected axle-like mobility assembly. Preserve separate drive versus mobility input jobs; do not add rubber, wheels, electronics or a full vehicle.

Evidence: [15b-mobility-wrong-output](evidence/15b-mobility-wrong-output.png), [locked-mobility-identity](evidence/locked-mobility-identity.png).

### IND-R1-06 — I04

The three infeed staging modules are distinct, but their terminations do not clearly resolve into three receiving staging locations. The lowest sheet/plank approach meets the bench foot/base area; the other two terminate at storage-rack levels. No supported transfer from those docks to the working assembly staging positions is demonstrated.

**Repair:** Align each conveyor with an explicit steel, parts, and selected third-material receiving tray using supported transitions. If a dock is a manual pickup staging area, show that handoff and clear access honestly rather than depicting a belt ending in a cabinet wall or base as automatic feed. Keep the handwheel/hoist control apron free.

Evidence: [15b-three-infeed-interfaces](evidence/15b-three-infeed-interfaces.png).

### IND-R1-07 — I04, I05, I06

The detachable crude drum reads materially larger relative to C1 than the compact selected03 crude unit. The drive output also reads larger than selected05's compact human-relative assembly. These are screen-space visual discrepancies, not measured world dimensions; current camera evidence cannot certify the locked size match. Fixed machine tanks/reservoirs may remain machine parts, but a detachable resource drum should not silently become a new bulk resource.

**Repair:** Rebind detachable resource sizes to the selected resource sheets: crude drum roughly 0.30–0.32 of C1 height; drive/mobility maximum silhouette roughly 0.30–0.32 of C1 height. Refit receiving cradles/couplings accordingly while leaving the fixed machine structure and C1 unchanged. Use a same-ground scale crop for final verification; do not claim physical runtime dimensions.

Evidence: [15b-pump-crude-scale](evidence/15b-pump-crude-scale.png), [locked-crude-scale](evidence/locked-crude-scale.png).

### IND-R1-08 — I06

The refinery has two fuel cans and a FULL signal, plus a closed valve inset, but the outgoing roller tray still ends in an open horizontal silver end plate. No physical end restraint or latched finite pickup cradle is visible to hold those cans.

**Repair:** Add an actual raised terminal stop/latched retaining cradle at the collection end, keep the output valve visibly closed, and show both cans safely retained without overlap. Preserve distinct crude-drum and clean-fuel-can silhouettes, finite staging and manual collection access.

Evidence: [15b-refinery-full-terminal](evidence/15b-refinery-full-terminal.png).

## Size qualification

Raster perspective cannot establish exact world-space dimensions. The scale finding compares visible detachable items with their locked human-relative source sheets; it does not certify collider tolerances or native dimensions. Keep fixed reservoirs separate from portable resource units when repairing the crude coupling.

## Retest scope

Retest the exact revised images for all I01–I06 checks, particularly: no stock identity change through a connected run; one selected metal-bench output; actual coal-receiver handoff; exact axle-like mobility output; supported or explicitly manual receiving docks; visible finite output retention; selected compact item scale. Add the missing smelter hold evidence. No averaging may hide a failed mandatory row.

Full source hashes, native crop coordinates and reviewer independence are in [INDUSTRIAL_I01_I06_REVIEW.json](INDUSTRIAL_I01_I06_REVIEW.json) and [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json). No candidate, selection or runtime approval was changed.
