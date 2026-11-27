# Reproduce the gameplay frames

Use Godot 4.7.2 and the reviewed Level 1 project. These small save copies contain earned game inventories. The starter checkpoint holds nine meat bundles and has only the furnace, first expansion and starter storehouse purchased. The expanded checkpoint holds nine timber, two stone, and two meat. The worker checkpoint has a paid and rescued forester.

Run the following in Bash with the current directory set to this folder. The example records the starter FOOD visit at the Galaxy Z Fold7 cover aspect. The engine writes numbered JPEGs and native inventory, waypoint, and event data to the printed temporary directory. The viewport needs a graphical display that can accommodate the requested window size.

```bash
set -eu
game_dir=/absolute/path/to/HavenlineLevel1
replay_dir="$(pwd)"
profile_dir="$(mktemp -d /tmp/havenline-l1-v3-replay-XXXXXX)"
capture_dir="$(mktemp -d)"
printf '%s\n' HAVENLINE-ALFRED-V3-DISPOSABLE > "$profile_dir/L1-DISPOSABLE"
cp "$replay_dir/starter-nine-meat.save.json" "$profile_dir/field-inventory-v1.json"
export STARTER_FOOD=1 NATIVE_MOVIE=1 ACTION_HZ=20 PROBE_DIR="$capture_dir"
godot --path "$game_dir" --windowed --resolution 360x840 --fixed-fps 20 --disable-render-loop --audio-driver Dummy --script "$replay_dir/field-camera.gd" -- "--l1-disposable-profile=$profile_dir"
echo "$capture_dir"
```

Start a new temporary profile for each take. For the cooker and warehouse run, use the expanded checkpoint and set `STARTER_FOOD=0`. For the four 1080 × 2520 starter photos, use `STARTER_FOOD=1`, `NATIVE_MOVIE=0`, `PORTRAIT_4K=1`, `ACTION_HZ=30`, and pass `--fixed-fps 30 --resolution 1080x2520`. For the six 2160 × 3840 forest photos, use the first-worker-delivery checkpoint, `STARTER_FOOD=0`, `NATIVE_MOVIE=0`, `PORTRAIT_4K=1`, `ACTION_HZ=24`, and pass `--fixed-fps 24 --resolution 2160x3840`. The forest stills stage the player at two viewing locations and pause the enemy wave clock while the follower and forester run their normal game states. The main field logic runs at 60 physics ticks per second.

Add the optional environment variable `WAREHOUSE_ONLY=1` to an expanded run to record only the loaded walk through the center door and wait for the last shelves to settle.
