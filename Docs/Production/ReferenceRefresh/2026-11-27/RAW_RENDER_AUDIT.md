# Havenline render audit for task-plan refresh

**Audit scope:** Read-only reference/asset research. This is not the final independent production critic or a recertification of gameplay.

## Outcome

Fourteen archived source groups supply 293 selected-sheet records, including retained historical versions and supplementary views. Every selected path and Git blob in the inventory resolves in the retained complete final archive tree at `a868ae89cdf2f120b478aa0a48fff35e09cc465c`. The current audit also fetched the latest README, original selected-status index and all three resource manifests directly from GitHub at that immutable commit. These counts do not mean 293 distinct imported models.

The November 27 package adds exactly **81 sheets covering 60 source-supported families**: 35 world sheets across 30 families and 65 depicted forms; 12 body/hand sheets for 6 existing NPC/survivor identities; 14 additional Atlas animal appearances; and 20 sheets for 10 Atlas raider appearances. Hidden rear faces, interior layouts and certain use states are authored interpretations. Atlas A/B/C denotes source appearances, not approved gameplay tiers.

## Source index

| Group | Sheets | Historical static scores | Primary task mapping |
|---|---:|---|---|
| [baseline-equipment-cast-companions](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/RenderArchive/2026-11-23/selected-status.json) | 68 | 9.2–9.5 | T05, T06, T08, T09, T15, T16, T17, T18, T19, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T53, T59, T60, T61 |
| [resources-2026-11-23](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23/delivery-manifest.json) | 13 | 9.2–9.5 | T05, T08, T09, T16, T17, T19, T21 |
| [resources-2026-11-23-expansion](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23-expansion/delivery-manifest.json) | 20 | 9.2–9.5 | T05, T08, T09, T16, T18, T19, T21 |
| [resources-2026-11-23-plots](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ResourceTurnarounds/2026-11-23-plots/delivery-manifest.json) | 29 | 9.2–9.6 | T08, T09, T10, T11, T17, T18, T22, T23, T31 |
| [enemy-original](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/InvaderTurnarounds/2026-11-24/selected-status.json) | 8 | 9.7–9.8 | T13, T21, T22 |
| [enemy-expanded](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/InvaderTurnarounds/2026-11-24/expansion/selected-status.json) | 20 | 9.6–9.7 | T13, T21, T22 |
| [enemy-authored-proposals](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/InvaderTurnarounds/2026-11-24/roster-expansion-02/selected-status.json) | 16 | 9.6–9.8 | T13, T21, T22 |
| [characters-1-4](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/CharacterTurnarounds/2026-11-24/reference-style-01/selected-status.json) | 12 | 9.7–9.8 | T06, T59, T60, T61 |
| [fence-gates-counters](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/StructureReferences/2026-11-25/selected-status.json) | 9 | 9.7–9.7 | T03, T11, T17, T20, T22 |
| [character1-supplied-18617](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/CharacterTurnarounds/2026-11-26/character-1-design-18617/generation-manifest.json) | 3 | 9.8–9.9 | T06, T08, T09 |
| [upgradeable-storehouse](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/StructureReferences/2026-11-26/upgradeable-storage-house/generation-manifest.json) | 4 | 9.9–9.9 | T08, T11, T16, T17, T18, T19 |
| [modern-ui-directions](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/UIConcepts/2026-11-26/modern-directions-01/generation-manifest.json) | 3 | 9.5–9.7 | T04, T07, T08, T15, T23, T54, T55, T58 |
| [connected-logistics](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/ConveyorReferences/2026-11-26/connected-logistics-01/generation-manifest.json) | 7 | 9.8–9.8 | T03, T05, T08, T11, T16, T17, T18, T19, T20 |
| [missing-source-coverage](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/generation-manifest.json) | 81 | 9.5–9.8 | T01, T02, T03, T05, T11, T15, T16, T19, T21, T22, T23, T24, T31, T44, T45, T48, T49, T50, T51, T53 |

The inventory JSON contains every selected file path, exact Git blob, SHA-256, byte size and historical static score. Task mappings are proposed from the recovered T01–T70 title table and must be reconciled with the active plan; task status has not been changed by this audit.

## Required plan changes

1. **Bind every visual task to selected reference bytes.** Require archive commit, selected PNG path/hash, applicable original-video windows, actual imported native asset path/hash and the exact runtime candidate SHA. Use selected/reviewed-concepts entries. Retain rejected attempts for history without feeding them into production accidentally. Existing valid artwork should not be regenerated merely because a model, rig or runtime proof is missing.

2. **Keep design identity separate from readiness.** A static reference PASS or archive-delivery 10 does not certify a rig, runtime system or 9.9 reference match. Original equipment and companions still carry historical 9.2–9.5 scores; newer Nov27 sheets range 9.5–9.8. Preserve these historical numbers. A current ≥9.9 output needs fresh matched-camera evidence and zero unresolved mandatory defects, not a relabeled score. The storage-house package is the one listed set whose four historical static reviews all reached 9.9.

3. **Use the latest Character 1 supplied-design binding.** The 18617 revision provides eight body directions and separate right/left palm/back glove views. Preserve royal blue/orange/cream appearance, right hip pouch, left hem patch, purple knees and exact supplied identity. Hand-reference inspection supports four separated fingers plus opposed thumb and correct chirality. It does not prove deformation. Keep current in-game scale unless separately approved evidence supports a change. Require full movement/harvesting/carry/attack cycles with feet/toe/knee, wrist/finger and contact checks in the native candidate.

4. **Use newer structural and NPC supplements correctly.** Nov25 fence/gate/counter set is the detailed structural reference. Nov27 NPC body/hand additions fill spread-finger reference gaps for the same six existing identities; they do not create six new characters. The formerly missing mounted defense platform now has a Nov27 turnaround and detail sheet, closing that static gap only. Preserve all earlier history.

5. **Make material transfers physically and logically coherent.** The conveyor package supplies 37 station dispositions, 25 directed routes and all 14 source equipment families. First deployment D06 is explicitly intake → cooker → storage → requested counter stock; expanded D02/D07 allows direct fresh output with controlled surplus storage and a gated fresh/stored merge. These are two documented stages, not interchangeable pictures. Require compatible typed ports, bounded buffers, destination reservation, wrong-item hold/recovery, full-buffer upstream stop, exactly-once custody and no automatic storage OUT→IN circulation. Rotation must rotate real ports and service faces; mirrored labels cannot repair geometry.

6. **Preserve circulation and storage interfaces.** Four separate proposed docks: utility IN/OUT low on the left, prepared-food IN/OUT at rear food-shelf height. Keep original front doors/apron, high window, rear vent, closed raw-food cabinets and right fuel hatch accessible. Food/utility/fuel/cash routes remain separate. Fuel, hides/fur, raw-food cabinets, cash and undefined outputs remain manual in this first automation upgrade. The central warming furnace is not a smelter. Keep two distinct usable bidirectional gate corridors and clear human/service approaches. A conceptual camp picture does not certify measured fit or collision.

7. **Respect source-specific pad forms and state behavior.** Storage is a nearly flush dark rounded rectangle with continuous rim and resource pictogram; buy/action uses four rounded corner brackets and source-like glyph/cost fields. Work zone is segmented, unfilled, no cost. Idle/active colors and one-shot versus repeatable completion behavior must match the appropriate source. Quantities shown in renders are illustrative; the source construction price does not demonstrate decrementing balance. Typed mixed carry and pad identity need native tests.

8. **Carry cast and world boundaries into progression.** Original and authored enemy sets are not an exhaustive source roster. Named Atlas appearances remain distinct identities; future buildings/defenses retain proposal status until the active progression task assigns them. No implied species meat eligibility, recipe, capacity, production rate, ammunition recipe, unlock level or numerical tier should be inferred solely from a sheet.

## Direct pixel inspection in this audit

Seven representative full sheets were opened: latest Character1 cardinal and hands; storehouse organization/stocked/empty/loading states; initial automation camp; wheat food processor opposing views/details; Atlas raider hands/gear; fortress gates open front/rear studies. These support the observed identity, chirality, type separation, physical connection and interpreted-surface points above. This was not a fresh complete visual review of all 293 sheets, and no animation or audio playback was performed in this render audit.

## Still-open evidence

- **T21/T22 planning owner:** Complete named handheld combat upgrade roster is not established; do not invent exhaustive coverage.
- **reference research owner + T21:** YT13 tiny overhead hostile identity unresolved; no exhaustive hostile roster claim.
- **T27/T31 animation owner:** Owl selected static turnaround lacks full open-wing/flight-cycle proof; motion task requires real full flight cycle, landing, perching and transitions.
- **integration/asset owners T01-T70:** Pinned art references must bind to actual imported native asset paths/hashes, final gameplay-camera captures and matching state/angle proof.
- **plan owner:** T71-T80 IDs not defined by the recovered known build-plan table; preserve missing-source status until actual source recovered or explicitly proposed.

The root audit is separately checking Build11 and its actual imports; no claim is made here that these references are absent from the current build.
