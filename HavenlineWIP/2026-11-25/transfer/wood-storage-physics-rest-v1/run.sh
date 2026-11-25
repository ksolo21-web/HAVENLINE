#!/bin/bash
set -euo pipefail
src=$(realpath "$1"); plate=$(realpath "$2")
d=$(cd "$(dirname "$0")";pwd); cd "$d"
w=$(mktemp -d ../hvn-storage-physics-local.XXXXXX)
w=$(realpath "$w")
realpath "$w" >/tmp/hvn-storage-physics-current
for k in home cache config data runtime tmp; do mkdir -m 700 "$w/$k"; done
cp project.godot fixture.gd "$w"
python pin_geometry.py "$src" "$plate" > "$w/fixture_data.json"
export HOME="$w/home" XDG_CACHE_HOME="$w/cache" XDG_CONFIG_HOME="$w/config" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
for k in baseline trial; do
 status=0
 HVN_MODE=$k timeout 30s godot --headless --fixed-fps 60 --path "$w" --script res://fixture.gd > "$w/$k.log" 2>&1 || status=$?
 printf '%s %s\n' "$k" "$status" | tee -a "$w/codes"
done
