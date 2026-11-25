# Enlarged wood: one adjusted seat candidate (offline rejection)

Inputs are SHA-pinned by `check.py`: exact crown GLB (both opaque bark/end-grain materials), exact native-derived manifest's terminal age 266 camera and seats, and the detached terrain-conforming visible marker mesh and original paint. No actor/camera/terrain/marker/ownership changes. Tested only the earlier scale-B candidate (uniform 3.522754× about source AABB center, with world base at prior seat origin), fixed X spread ±65 mm, fixed original heading, and two pitch/roll plus Y adjustments solved for the same three actual original contact points. The extra 5.385 mm per seat over the mathematical minimum planned shift reserves a small cushion for pitch/roll. No second placement searched.

Exact clipped polygons overlay the log faces on actual piecewise-linear visible marker/floor triangle cells. Old original unmodified seats reproduce zero support to within 4 nm. At candidate scale and spread, 3 contact constraints solved while preserving 30.780 mm minimum world-X pair separation, larger than the required 20 mm. Both finished logs project to ~52.58 px major diameter from the same 1280×720 stock camera. However noncontact lower triangles enter the visible deck 0.210 / 0.208 mm, despite the explicit three-point solve. The collision base remains below the visible deck by 12 mm; no claim of physical settling or supported nav/collision.

Visual fit also fails on the unchanged painted wood icon. Centered icon color segmentation of the exact 1320×1040 opaque texture into 115,267 icon sample centers (excludes trim/background) is mapped via the exact marker UV transform and visible piecewise-linear terrain height. Compare the projected samples and camera depth against every actual log triangle, separately for the two logs. Near log blocks 39,652 of those samples (34.40% of the selected texture samples, not the percentage of final screen pixels). Far log blocks zero. We do not claim lighting, resampling, dynamic occlusion, Character1 silhouette, native pixels or readability score. The test fails on real log/paint depth interference even if the submillimeter contact issue were fixed.

Reproduce from workspace root:
```sh
OPENBLAS_NUM_THREADS=1 python hvn-l1-wood-larger-seat-support-v1/check.py EXACT_ORIGINAL_CROWN_GLB EXACT_MANIFEST EXACT_TERRAIN_STAGE
```
Only README.md, check.py, result.json and SHA256SUMS are portable. No runtime sources, asset bytes, media, copied owner video, or raw native capture included.
