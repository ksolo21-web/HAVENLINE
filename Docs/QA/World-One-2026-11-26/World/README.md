# The World One snowfield

The surveyed playable square runs from −512 to +512 metres on each map axis. Its 1,024 streaming cells contain 31,901 pines and 2,579 stone banks outside the authored opening. All 34,480 positions and source IDs came from the same generator used by the live scene. A cluster of strong green points marks a dense stand of timber. Copper points mark quarry sites. The statistics exclude the planted opening forest and starter sources.

[Open the full map](World-One-map.jpg) · [Download outer-world coordinates](World-One-sources.csv.gz)

The engine keeps at most nine 32 m cells resident. It draws distant sources in batches and switches nearby ones to the individual harvest objects. A revisit preserves the original source, partial strikes and remaining regrowth time. The native checks exercised the four corners, the physics ground, revisits during both cooldowns and ordinary joystick travel across the old level boundary.

These two normal-camera frames are positioned inspections of the far world. The gameplay film separately records a player-controlled expedition from camp and back.

[Western forest](West-forest.jpg) · [Northeastern snow ridge](Northeast-boundary.jpg) · [Streaming checks](World-streaming.json)

On the expanded court, one native 1280 × 720 Ultra inspection submitted 311,947 visible primitives at 1× and 251,079 at 2×. The figures include the whole visible field at the sampled player position; the active pack, camera and view affect them. The supplied cost report records visible and shadow counters separately. These Linux software-renderer samples measure scene workload. Sustained frame times and thermals require target-device runs. [Native draw counters](Rendered-scene-cost.json)

All 18 gameplay suites passed their assertions. Two fixed-speed test runs retained audio references as the process exited. The world test exited cleanly when paced, and the original two-process save and resume test exited cleanly with wall-clock pacing. The initial and repeated results are included. [Native suite receipts](Native-suite-results.json)

## Tuning locations

- `world_landscape.gd` defines the world seed, cell size, placement and near-source distances. `layout.json` contains the map extent and initial camp layout.
- `field_lifecycle.gd` defines resource and loose-drop lifetimes. `field_encounters.gd` sets wave timing, group limits and boss probability. `field_enemy.gd` sets wolf sizes, health and combat behavior.
- `field_progression.gd` sets construction prerequisites and prices. `field_environment.gd` owns the earned perimeter, gate presentation, floor and gate positions.
- `weapon_orbit.gd` and `orbit_opening.gd` define the displayed tool and swept contact. `field_opening.gd` applies the earned boundary and connects combat, inventory, music and events.
- `field_snow_tracks.gd` controls foot and paw registration, snow eligibility, size, aging and per-cell limits. `field_defense_tower.gd` controls tower range, reload, targeting and projectile hits.
