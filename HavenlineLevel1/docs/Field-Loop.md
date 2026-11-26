# Havenline · World One

Open `res://field_opening.tscn` in Godot 4.7.2. The pinned source and extraction instructions are in `Docs/QA/World-One-2026-11-26/Build/`. This trial follows Alfred’s Level 1 work. It has its own save identity, `Havenline-World-One-Review`.

## From the first tree to the eastern watchtower

Move with a one-finger drag or WASD. A short drag walks and a longer drag runs. Pinch or use the wheel to zoom. Approach a gate to operate it with the on-screen control or E. The two leaves open together and the passage is usable from either side.

Start on snow and gather wood. Outside a purchased camp, the equipped tool sweeps at waist height. Its visible head must reach a source for a strike to count. Three hits fell a pine or deplete a stone bank. Collect the wood after the fall or the loose stone after mining. Wolves drop meat when defeated. Each resource stays on its own section of the pack. Stand on a purchase plot while carrying or storing the required resources. The last payment arrives before the purchase completes.

| Purchase | Price | What appears |
| --- | --- | --- |
| Hearth | 3 wood | A centered furnace, 10 × 8 m court, enclosing fence, and south and east gates |
| First expansion | 3 wood, 1 stone | A 13 × 10.5 m court with three separate corner offers |
| Wood storage | 2 wood | Northwest wood plot |
| Stone storage | 2 wood, 1 stone | Northeast stone plot |
| Meat storage | 2 wood, 1 meat | Southwest meat plot |
| Second expansion | 3 wood, 2 stone | After all three storage purchases, a 15.5 × 12.4 m court, eastern tower offer and extra-axes offer |
| Eastern watchtower | 3 wood, 2 stone | A working defensive launcher facing the main approach |
| Additional axes | 2 stone, 1 meat | Three orbiting tools outside the perimeter |

The southeast corner is reserved for future money storage. Each purchased floor plot accepts its corresponding material. The player’s tools and hit detection stop at the earned boundary and resume upon exit. The tower continues to defend the camp while the player is inside.

## World and encounter settings

| Setting | Trial value |
| --- | --- |
| Snowfield | 1,024 × 1,024 m, deterministic seed 860342 |
| Streaming | 32 m cells, at most 3 × 3 cells resident. Nearby trees and quarries become individual interactable sources |
| Wood | 22 played seconds after depletion |
| Stone | 32 played seconds after depletion |
| Meat | 2 per normal wolf or 5 per alpha. Replenished through encounters |
| Encounter interval | 24 played seconds. A pack requests 2–4 wolves, up to 4 live wolves globally |
| Boss | 18% chance per successful encounter. One alpha can replace a pack member, at 1.58× ordinary size and 8 HP versus 3 |
| Tower | 13 m range, 1.65 s reload. The bolt deals damage on arrival |
| Loose drops | Up to 72, with a 100 s lifetime |
| Tracks | Boot and paw impressions on snow, with larger paws for the alpha. Tracks fade over 17 s, with a maximum of 720 active and 96 per 12 m cell |

Resource and encounter timers use simulation time. Leaving a region preserves partial harvests and remaining cooldowns. Closing and reopening restores purchases, stocks, pack, player position and health, loose drops and remaining encounter time. A fallen player recovers through the normal recovery sequence. The opening prices and rates above are gameplay tuning decisions. The locked reference clips guide timing, camera proportions, and the order of visual feedback. Source comparisons are under `Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/`.

## Replaying the purchase route

From the extracted project, use a fresh disposable profile. These commands exercise movement, gates, purchasing and combat through game input and write observations below the temporary QA directory.

```bash
project_dir="$PWD"
qa_dir=$(mktemp -d)
profile_dir=$(mktemp -d /tmp/havenline-l1-v3-world-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile_dir/L1-DISPOSABLE"
export XDG_DATA_HOME="$qa_dir/data" XDG_CONFIG_HOME="$qa_dir/config" XDG_CACHE_HOME="$qa_dir/cache"
export FIELD_QA_PLAN="$project_dir/tests/world_route.json" FIELD_QA_OUTPUT="$qa_dir" FIELD_QA_HEADLESS=1
godot --headless --editor --path "$project_dir" --import
godot --headless --path "$project_dir" --fixed-fps 24 --script res://tests/world_route.gd -- "--l1-disposable-profile=$profile_dir"
```

The five music loops and event recordings are under `assets/audio/`. To regenerate the authored bank, install NumPy and SciPy and run `python3 tools/audio/render_field_score.py --output /tmp/havenline-world-audio-review`. The field mixer includes separate boss arrival, boss defeat, tower release and tower impact cues.
