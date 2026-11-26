# The World One snowfield

The surveyed playable square runs from −512 to +512 metres on each map axis. Its 1,024 streaming cells contain 31,901 pines and 2,579 stone banks outside the authored opening. All 34,480 positions and source IDs came from the same generator used by the live scene. A cluster of strong green points marks a dense stand of timber. Copper points mark quarry sites. The statistics exclude the planted opening forest and starter sources.

[Open the full map](World-One-map.jpg) · [Download outer-world coordinates](World-One-sources.csv.gz)

The engine keeps at most nine 32 m cells resident. It draws distant sources in batches and switches nearby ones to the individual harvest objects. A revisit preserves the original source, partial strikes and remaining regrowth time. The native checks exercised the four corners, the physics ground, revisits during both cooldowns and ordinary joystick travel across the old level boundary.

These two normal-camera frames are positioned inspections of the far world. The gameplay film separately records a player-controlled expedition from camp and back.

[Western forest](West-forest.jpg) · [Northeastern snow ridge](Northeast-boundary.jpg) · [Streaming checks](World-streaming.json)

On the expanded court, one native 1280 × 720 Ultra inspection submitted 301,691 visible primitives at 1× and 244,791 at 2×. The figures include the whole visible field at the sampled player position; the active pack, camera and view affect them. The supplied cost report records visible and shadow counters separately. These Linux software-renderer samples measure scene workload. Sustained frame times and thermals require target-device runs. [Native draw counters](Rendered-scene-cost.json)

The outer-world test passed all 23 assertions. Its first accelerated headless teardown reported seven resources still in use. A paced repeat passed the same 23 assertions with a clean shutdown. [Native suite receipts](Native-suite-results.json)
