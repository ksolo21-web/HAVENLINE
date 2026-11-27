# Exact depth guard retest

The additional foreground depth test leaves the gunner visually clean and retains the cyan cue over the parts actually covered by the tower or bow. All 11 tower and weapon meshes stayed opaque and non-emissive. The exact pixel checks found one exposed edge pixel at each northeast zoom, which leaves the strict zero-change condition open. Both southeast views pass that condition. [Northeast 2× detail](NE-2x-detail.png) · [Southeast 2× detail](SE-2x-detail.png)

| Gameplay view | Exposed guard pixels with any RGB change | Covered guard pixels with the cue |
| --- | ---: | ---: |
| Northeast 1× | 1 of 1,484 | 3 of 12 |
| Northeast 2× | 1 of 6,115 | 17 of 45 |
| Southeast 1× | 0 of 1,324 | 267 of 336 |
| Southeast 2× | 0 of 5,437 | 1,192 of 1,337 |

Two render controls identify the visible and covered guard exactly. The first paints the guard magenta with normal tower depth. The second omits the tower meshes from the gameplay camera so the full guard silhouette is visible. Each paired screenshot uses the same paid camp scene, aim pose, and normal game camera at 720×960 in Godot’s desktop OpenGL compatibility renderer. The detail images show the effect, the same pose with the effect disabled, and the comparison with visible differences in red and covered-pixel changes in yellow. [Northeast 1× gameplay](NE-1x-effect.png) · [Northeast 2× gameplay](NE-2x-effect.png) · [Southeast 1× gameplay](SE-1x-effect.png) · [Southeast 2× gameplay](SE-2x-effect.png) · [Source hashes and measurements](Exact-depth-native-measurements.json)

Scope includes the tower and guard sightline only. The prior character and survivor animation reviews retain their separate 9.9 threshold. The comparison uses Havenline’s selected roofless ballista and the armed platform from locked video B at 43.00 seconds. [Owner’s ballista sheet](https://github.com/ksolo21-web/HAVENLINE/blob/2ae9702b0b6294b6cca3fa0d3098025d72484f06/Docs/Design/RenderArchive/2026-11-23/selected/equipment/ballista_tower.png) · [Locked reference frames](../../../camp12/References/Owner-matched-B-defense.jpg)
