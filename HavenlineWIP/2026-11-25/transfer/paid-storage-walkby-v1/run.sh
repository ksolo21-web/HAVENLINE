#!/bin/bash
set -euo pipefail
# Require affirmative sole functional grant before invoking.
d="$(cd "$(dirname "$0")";pwd)"
p="$(realpath "$1")"
w="$(realpath "$2")"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test -d "$p/.godot"
test ! -e "$w/native.log"
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w/runtime"
python "$d/prepare.py" "$p" "$w/run_probe.gd"
cmp "$d/probe.gd" "$w/run_probe.gd"
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" timeout 110s godot --headless --fixed-fps 60 --path "$p" --script "$w/run_probe.gd" > "$w/native.log" 2>&1
grep '^WALK_SUM ' "$w/native.log"
! grep -E 'ERROR|WARNING|FAIL' "$w/native.log"
