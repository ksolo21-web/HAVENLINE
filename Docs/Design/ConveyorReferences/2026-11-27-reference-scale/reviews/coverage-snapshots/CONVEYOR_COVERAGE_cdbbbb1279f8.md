# Current Conveyor Static Coverage

**34 / 36 rows PASS. One HOLD and one PARTIAL remain. Runtime remains unproved.**

This is a scoped static coverage checkpoint, not final whole-task or publication approval. Prior snapshots are preserved in history.

| Row | Module or interface | Static status | Score | Remaining requirement |
|---|---|---|---:|---|
| T01 | Level straight | PASS | 10 | Mandatory static evidence passed. |
| T02 | 90-degree left corner | PASS | 10 | Mandatory static evidence passed. |
| T03 | 90-degree right corner | PASS | 10 | Mandatory static evidence passed. |
| T04 | Rising height adapter | PASS | 10 | Mandatory static evidence passed. |
| T05 | Falling height adapter | PASS | 10 | Mandatory static evidence passed. |
| T06 | End coupler and bridge plate | PASS | 10 | Mandatory static evidence passed. |
| R01 | One-input/two-output diverter | PASS | 10 | Mandatory static evidence passed. |
| R02 | Two-input/one-output gated merge | PASS | 10 | Mandatory static evidence passed. |
| R03 | Finite stock/output buffer and stop gate | PASS | 10 | Mandatory static evidence passed. |
| R04 | Wrong-item hold / bounded reject landing | PASS | 10 | Mandatory static evidence passed. |
| R05 | Grade-separated conveyor crossing | PASS | 10 | Mandatory static evidence passed. |
| S01 | Utility storage IN | PASS | 10 | Mandatory static evidence passed. |
| S02 | Utility storage OUT | PASS | 10 | Mandatory static evidence passed. |
| S03 | Prepared-food storage IN | PASS | 10 | Mandatory static evidence passed. |
| S04 | Prepared-food storage OUT | PASS | 10 | Mandatory static evidence passed. |
| S05 | Local utility indexed tray/lift | PASS | 10 | Mandatory static evidence passed. |
| S06 | Local prepared-food tray/shuttle | PASS | 10 | Mandatory static evidence passed. |
| F01 | Shore intake and front discharge | HOLD | 9.0 | Only LEFT SIDE in 06 R7b has 12 rather than the authored 13 cylinders. Rear, front and right read 13. Owner01 loaded baseline and native front-discharge/C1 detail are already reviewed; no new shoreline environment is required. |
| F02 | Cooker raw-food input dock | PASS | 10 | Mandatory static evidence passed. |
| F03 | Cooker processed-food output dock | PASS | 10 | Mandatory static evidence passed. |
| F04 | Meat-to-meal dock use | PASS | 10 | Mandatory static evidence passed. |
| F05 | Wheat processor raw and bread output docks | PASS | 10 | Mandatory static evidence passed. |
| U01 | Typed raw utility feeder | PASS | 10 | Mandatory static evidence passed. |
| U02 | Saw wood input and plank output docks | PASS | 10 | Mandatory static evidence passed. |
| U03 | Quarry/stone processor input and block output docks | PASS | 10 | Mandatory static evidence passed. |
| I01 | Coal smelter typed interfaces | PASS | 10 | Mandatory static evidence passed. |
| I02 | Metal bench input and alternative outputs | PASS | 10 | Mandatory static evidence passed. |
| I03 | Steel forge typed interfaces | PASS | 10 | Mandatory static evidence passed. |
| I04 | Industrial assembly multiple-input docks | PASS | 10 | Mandatory static evidence passed. |
| I05 | Manual pump crude container handoff | PASS | 10 | Mandatory static evidence passed. |
| I06 | Refinery crude/coal inputs and fuel output | PASS | 10 | Mandatory static evidence passed. |
| A01 | Reserved two-input food assembler | PASS | 10 | Mandatory static evidence passed. |
| C01 | Self-service food counter restock and separate cash | PASS | 10 | Mandatory static evidence passed. |
| C02 | Catalogue-gated material counter dock use | PASS | 10 | Mandatory static evidence passed. |
| N01 | First connected camp route | PASS | 10 | Mandatory static evidence passed. |
| N02 | Expanded compatible machine-to-storage/counter network | PARTIAL | 8.5 | R2 joins need the actual counter receiving ends, actual timber house IN mouth, approved rear-left bench iron receiver, and visible cassette OUT mouth. Planner is revising the consolidated layout. Industrial and quarry component dependencies now pass. |

Industrial I01–I06 retain reviewer `/root/resource_inventory` provenance. This aggregator did not substitute its own image judgment for that independent review.

All source image and report hashes are frozen in the JSON companion. Runtime approval is false for every row.
