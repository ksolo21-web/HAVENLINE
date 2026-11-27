# Final guard sightline review

The guard sightline earned **9.5/10** for gameplay presentation in the tested desktop views. The exposed guard looks solid at normal and 2× zoom. Cyan still identifies the guard where the bow covers them. All 11 tower and weapon meshes stayed opaque with emission disabled. A single exposed edge pixel changed in the northeast 1× frame. The three other views had zero changes on the visible guard. [Northeast 1×](NE-1x-effect.png) · [Northeast 2×](NE-2x-effect.png) · [Southeast 1×](SE-1x-effect.png) · [Southeast 2×](SE-2x-effect.png)

| Gameplay view | Exposed guard pixels with any RGB change | Covered guard pixels with the cue |
| --- | ---: | ---: |
| Northeast 1× | 1 of 1,484 | 1 of 12 |
| Northeast 2× | 0 of 6,115 | 13 of 45 |
| Southeast 1× | 0 of 1,324 | 267 of 336 |
| Southeast 2× | 0 of 5,437 | 1,192 of 1,337 |

The 360×480 tower mask changed after each turn or zoom and was byte-identical across held frames. I used a paid east tower in an isolated profile with Godot’s desktop OpenGL compatibility renderer at 720×960. I used magenta render controls to distinguish the guard pixels the main camera actually sees from the pixels covered by the tower. The detail comparisons show the effect, the same pose with the effect disabled, and changes marked in red for exposed pixels and yellow for covered pixels. [Northeast 1× detail](NE-1x-detail.png) · [Southeast 2× detail](SE-2x-detail.png) · [Native results and tested source hashes](Guard-final-measurements.json)

This verdict covers the guard effect and tower material. Character and survivor animation retain their separate 9.9 target. The comparison used the owner’s roofless ballista and the armed platform in locked video B at 43.00 seconds. [Owner’s ballista sheet](https://github.com/ksolo21-web/HAVENLINE/blob/2ae9702b0b6294b6cca3fa0d3098025d72484f06/Docs/Design/RenderArchive/2026-11-23/selected/equipment/ballista_tower.png) · [Locked reference frames](../../../camp12/References/Owner-matched-B-defense.jpg)
