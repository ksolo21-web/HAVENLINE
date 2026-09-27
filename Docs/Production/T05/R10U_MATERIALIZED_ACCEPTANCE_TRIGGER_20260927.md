# T05 R10U materialized exact-source acceptance trigger — 2026-09-27

Status: **ACTIVE / NOT APPROVED**

## Exact materialized source

The deterministic visual-repair materializer completed successfully and pushed:

- exact materialized commit: `8c29e0f46f90f196ab27fcebfbf9f88d622495fc`
- catalog triangles: **117,296**
- asset count: **22**
- generated storage bytes: **3,851,132**
- opposite-winding triangles: **0**
- nominal batched draw calls: camp **11**, lakeshore **10**
- furnace/hearth: **25,968 triangles**, SHA-256 `6d32499229dd22dde1ee32940bb1b0a506a0647ea911a4787b3bce83fe60a8e7`

The materializer changed only the expected deterministic station outputs for the R10T rendered-defect repair:
`catalog.json`, `cooker_processor.glb`, `defense_platform.glb`, `fishing_rack.glb`,
`processing_counter.glb`, and `service_counter.glb`.

## Purpose of this checkpoint

The materializer bot push intentionally does not recursively trigger the station-kit acceptance workflow.
This externally authored checkpoint changes no game source or generated asset bytes. Its only purpose is to
trigger the exact-source T05 precritic from the committed R10T materialization.

## Required acceptance

The triggered run must remain fail-closed and require:

- all 18 inherited + T05 suites green,
- 1,134/1,134 checks or more with no failures,
- actual Godot component/native evidence,
- R01 furnace identity preserved,
- no primitive/default/fallback leakage,
- no unauthorized gameplay/source drift.

After this gate passes, proceed immediately to the full **77-frame** component/family/integrated/native
evidence path and independent visual critic. T05 remains ACTIVE until those visual gates pass >9.0.
