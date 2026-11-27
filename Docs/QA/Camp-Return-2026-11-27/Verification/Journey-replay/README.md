# Repeat the earned field audit

The driver extends the reviewed game’s ordinary touch replay. It reads progress and chooses normal screen touches and drags. Run from this folder with Godot 4.7.2 and an imported copy of the reviewed native Godot project. All output goes to new temporary folders.

```bash
set -eu
game_dir=/absolute/path/to/HavenlineLevel1
replay_dir="$(pwd)"
export FIELD_QA_PLAN="$replay_dir/corrected.json"
export FIELD_QA_OUTPUT="$(mktemp -d)"
export JOURNEY_PROFILE="$(mktemp -d /tmp/havenline-l1-v3-journey-XXXXXXX)"
printf '%s\n' HAVENLINE-ALFRED-V3-DISPOSABLE > "$JOURNEY_PROFILE/L1-DISPOSABLE"
export FIELD_QA_HEADLESS=1
godot --headless --audio-driver Dummy --fixed-fps 60 --disable-render-loop --path "$game_dir" --script "$replay_dir/journey.gd" -- "--l1-disposable-profile=$JOURNEY_PROFILE"
echo "$FIELD_QA_OUTPUT"
```

The default run starts empty and earns the first four purchases. It records state at each phase and each second. To reproduce the distant return, set `FIELD_QA_PLAN` to `final-compass.json` and copy the previous run’s `built-storage_stone.save.json` into another new marked temporary profile named `field-inventory-v1.json`. The injury, migration, customer and terminal routes expect the starting states identified in the audit report. Use new disposable copies for each one. [Recorded routes and initial states](../Journey-audit.json)
