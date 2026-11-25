#!/bin/bash
# Explicit sole lease only. Existing disposable imported source, fresh own user://.
set -euo pipefail
d="$(cd "$(dirname "$0")";pwd)"
p="$(realpath "$1")"
w="$(realpath "$2")"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test -d "$p/.godot"
test ! -e "$w/native.log"
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w/runtime"
python "$d/prepare.py" "$p" "$w/run_probe.gd"
rc=0
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" timeout 110s godot --headless --fixed-fps 60 --path "$p" --script "$w/run_probe.gd" > "$w/native.log" 2>&1 || rc=$?
echo "$rc" > "$w/exit.txt"
grep -E '^WALK_(OBSTRUCTION|SUM) ' "$w/native.log"
test "$rc" -eq 1
test "$(grep -c '^TURN_DETAIL ' "$w/native.log")" -eq 6
! grep -E 'ERROR|WARNING' "$w/native.log"
grep -E '^(TURN_DETAIL|WALK_OBSTRUCTION|WALK_SUM) ' "$w/native.log" > "$d/native.txt"
