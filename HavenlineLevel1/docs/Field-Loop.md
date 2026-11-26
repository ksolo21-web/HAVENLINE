# Havenline · World One

Open `res://field_opening.tscn` in Godot 4.7.2. The pinned source and extraction instructions are in `Docs/QA/World-One-2026-11-26/Build/`. This trial follows Alfred’s Level 1 work. It has its own save identity, `Havenline-World-One-Review`.

## From the first tree to the eastern watchtower

Move with a one-finger drag or WASD. A short drag walks and a longer drag runs. Pinch or use the wheel to zoom. Approach a gate to operate it with the on-screen control or E. The two leaves open together and the passage is usable from either side.

Start on snow and gather wood. Outside a purchased camp, the equipped tool sweeps at waist height. Its visible head must reach a source for a strike to count. Three hits fell a pine or deplete a stone bank. Collect the wood after the fall or the loose stone after mining. Wolves drop meat when defeated. Each resource stays on its own section of the pack. Stand on a purchase plot while carrying or storing the required resources. The last payment arrives before the purchase completes.

| Purchase | Price | What appears |
| --- | --- | --- |
| Hearth | 3 wood | A centered furnace, 10 × 8 m court, enclosing fence, and south and east gates |
| First expansion | 3 wood, 1 stone | A 13 × 10.5 m court with one northwest storehouse offer |
| Starter storehouse | 2 wood | Rope-bound house with a timber bay |
| Reinforced storehouse | 2 wood, 1 stone | The same building gains iron bands, a masonry base and a stone bay |
| Advanced storehouse | 2 wood, 1 meat | Riveted blue siding and a cold-food bay |
| Second expansion | 3 wood, 2 stone | After all three storage purchases, a 15.5 × 12.4 m court, eastern tower offer and extra-axes offer |
| Eastern watchtower | 3 wood, 2 stone | A working defensive launcher facing the main approach |
| Additional axes | 2 stone, 1 meat | Three orbiting tools outside the perimeter |

Both double-leaf gates work at every camp size. The centered furnace occupies 76% of the preceding version’s linear dimensions. The mineable banks are larger in both the near geometry and streamed view. A physical pick stroke must still reach the rock.

The storehouse occupies one northwest site. Return to the right side of its loading apron to pay for the next tier, or enter the left side to unload into owned bays. Step out before visiting again. Its sliding doors and cutaway reveal timber, stone, and meat in separate bays. Stored balances survive later upgrades and individual units fly out to pay for purchases. The first stages present one buy plot at a time. The final expansion offers the eastern tower and additional axes. [Storehouse art](https://github.com/ksolo21-web/HAVENLINE/tree/30f4f037baf54b24652360c8b6880771e29cc19a) · [Fence and gate art](https://github.com/ksolo21-web/HAVENLINE/tree/26bb649e0a8090c9c9af7e91e62f384fc86372d8/Docs/Design/StructureReferences/2026-11-25/selected)

The player has four HP. Outside camp, wolves approach, brace and lunge. A normal bite costs one HP and an alpha bite costs two. Each registered hit shows a damage number, animates the struck character and plays an impact cue. The HUD keeps the health bar visible during exploration and combat. Zero HP stops the orbit and plays the fall. After the fall, the player returns to the original hearth plot if unpaid or inside the purchased camp at full health with two seconds of protection. Orbit contacts stop inside the paid perimeter and resume as the player exits.

## World and encounter settings

| Setting | Trial value |
| --- | --- |
| Snowfield | 1,024 × 1,024 m, deterministic seed 860342 |
| Streaming | 32 m cells, at most 3 × 3 cells resident. Nearby trees and quarries become individual interactable sources |
| Wood | 5 played seconds after depletion, including the final 0.45-second return animation |
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
export FIELD_QA_PLAN="$project_dir/tests/world_house_route.json" FIELD_QA_OUTPUT="$qa_dir" FIELD_QA_HEADLESS=1
godot --headless --editor --path "$project_dir" --import
godot --headless --path "$project_dir" --fixed-fps 24 --script res://tests/world_house_route.gd -- "--l1-disposable-profile=$profile_dir"
python3 tests/world_route_verify.py "$qa_dir"
python3 tests/world_final_gate_verify.py "$qa_dir"
python3 tests/world_house_verify.py "$qa_dir"
```

The five music loops and event recordings are under `assets/audio/`. To regenerate the authored bank, install NumPy and SciPy and run `python3 tools/audio/render_field_score.py --output /tmp/havenline-world-audio-review`. The field mixer includes separate boss arrival, boss defeat, tower release and tower impact cues.
