# Guard sightline retest

The tower-only depth mask removed the broad cyan bands across the exposed gunner. The see-through cue remains visible where the bow or tower covers the gunner. All 11 weapon and tower meshes stayed opaque with emission disabled. Small traces still cross exposed pixels beside the boots and gloves, so the retest falls short of the zero-tint requirement. [Northeast at 2×](NE-2x-detail.png) · [Southeast at 2×](SE-2x-detail.png)

| Gameplay view | Cyan on directly visible guard pixels | Cyan outside the directly visible guard mask |
| --- | ---: | ---: |
| Northeast 1× | 11 of 1,325 (0.83%) | 98 px |
| Northeast 2× | 49 of 5,821 (0.84%) | 19 px |
| Southeast 1× | 12 of 1,136 (1.06%) | 308 px |
| Southeast 2× | 53 of 4,958 (1.07%) | 1,301 px |

I repeated the original camera position and aim directions at 720×960 in Godot’s desktop OpenGL compatibility renderer. The detail images show the live effect, the same pose with the effect disabled, and the detected changes over visible guard pixels marked in red. The two roofless tower references supply the deck, mount, and bow proportions. The source leaves the sightline cue to Havenline’s gameplay design. [Northeast at 1×](NE-1x-effect.png) · [Southeast at 1×](SE-1x-effect.png) · [Native results and tested source hashes](Tower-mask-measurements.json)

This retest covers the guard sightline and tower opacity. The character and survivor animation reviews keep their separate 9.9 target. [Selected ballista sheet](https://github.com/ksolo21-web/HAVENLINE/blob/2ae9702b0b6294b6cca3fa0d3098025d72484f06/Docs/Design/RenderArchive/2026-11-23/selected/equipment/ballista_tower.png) · [Fitted platform](https://github.com/ksolo21-web/HAVENLINE/blob/2ae9702b0b6294b6cca3fa0d3098025d72484f06/Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/selected/defense-platform-details.png) · [Locked video B at 43.00 seconds](../../../camp12/References/Owner-matched-B-defense.jpg)
