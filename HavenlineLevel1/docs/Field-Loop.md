# Havenline field opening

The scene is `res://field_opening.tscn`. Run `HavenlineLevel1/project.godot` in Godot 4.7.2. The level starts on snow with Character 1 in the blue parka. One finger controls movement. Short drags walk and longer drags run. Two fingers pinch the gameplay camera. A keyboard and mouse can use WASD or arrows, the mouse wheel and E at either gate.

The orbit carries one equipped tool. Approach a pine or the stone bank and let the visible tool head cross it three times. When a tree starts falling, give it room to settle. Walk to the fallen wood or loose stones to put individual units on the pack. Wolves on the eastern snowfield approach, brace and lunge. The axe can damage a wolf on a sweep. A defeated wolf drops meat, and a defeated player recovers at the starting clearing.

Stand on the marked hearth plot with three wood. The last arriving unit pays for the furnace and fenced camp. Each material has its own flush storage plot inside the walls. Stand on the appropriate plot to unload. The crossed-axes plot accepts two stone and one meat from the pack or deposited stock. Completing that payment unlocks three orbiting tools. These are the playable branch's recipe amounts. The first comes from the Havenline opening layout. The second is a local progression choice.

A session starts fresh by default. Tests can persist to an explicitly marked disposable directory, using a field-specific filename. To replay the route from the project directory on Linux, run the following in a clean review profile.

```bash
project_dir="$PWD"
qa_dir=$(mktemp -d)
profile_dir=$(mktemp -d /tmp/havenline-l1-v3-field-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile_dir/L1-DISPOSABLE"
export XDG_DATA_HOME="$qa_dir/data" XDG_CONFIG_HOME="$qa_dir/config" XDG_CACHE_HOME="$qa_dir/cache"
export FIELD_QA_PLAN="$project_dir/tests/field_route.json" FIELD_QA_OUTPUT="$qa_dir" FIELD_QA_HEADLESS=1
godot --headless --editor --path "$project_dir" --import
godot --headless --path "$project_dir" --fixed-fps 60 --script res://tests/field_route.gd -- "--l1-disposable-profile=$profile_dir"
```

The source measurements and reference links are under `Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/`. The original Havenline art controls resource identity and the creature design. The recorded ads guide screen proportions, timing and the relationship between an action and its reward.
