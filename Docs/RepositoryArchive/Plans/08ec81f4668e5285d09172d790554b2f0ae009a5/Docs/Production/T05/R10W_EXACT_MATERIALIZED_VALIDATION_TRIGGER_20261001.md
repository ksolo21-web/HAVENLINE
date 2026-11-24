# T05 R10W exact materialized validation trigger — 2026-10-01

Status: **ACTIVE / NOT APPROVED**

This checkpoint contains no gameplay or visual-asset changes. It triggers the exact-source validation stack after the R10W watchtower/defense-platform repair was deterministically materialized and the shared CI fixes were moved into the integration baseline.

Exact materialized candidate lineage:
- R10W generated visual repair commit: `bc1a8ea4730d7290a1983cc067005ff71839615b`
- deterministic materialized GLB/catalog commit: `1f8722f92ecac1f6ea4d56cbfa0c3e3446a95389`
- exact-count rebind: `894ec07de5f74c3aab30f0abdd4d0349349668c8`
- clean integration-baseline merge: `3abcfdb4d679aee9bd367cda6a39b49822dcc617`

Current materialized source facts:
- 22 station/prop assets
- 120,292 catalog triangles
- 5,164,404 generated asset bytes
- 0 opposite-winding triangles
- camp batched draw calls: 11
- lakeshore batched draw calls: 10
- defense/watchtower: 11,244 triangles
- furnace/hearth identity preserved at 25,968 triangles

Required gate:
- isolated candidate guard PASS
- 18/18 inherited + T05 suites PASS
- full 77-frame actual-Godot evidence PASS: 12 component + 42 family + 20 integrated gameplay + 3 native 4K
- cheap pixel/performance gates PASS
- phone/tablet delivery PASS
- Native Android review PASS
- newest Havenline render authority comparison
- independent critic strictly >9.0 with no mandatory defect remaining

T05 remains ACTIVE until all required gates pass. T06 remains locked.
