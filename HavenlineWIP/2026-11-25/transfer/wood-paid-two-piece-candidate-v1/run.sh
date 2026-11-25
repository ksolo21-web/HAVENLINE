#!/bin/bash
# Invoke only under a separately assigned exclusive Godot functional lease.
set -euo pipefail
w=$(realpath "$1")
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test ! -e "$w/visual_probe.log"
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" timeout 90s godot --headless --fixed-fps 60 --path "$w/project" --script res://tests/paid_two_visual_probe.gd > "$w/visual_probe.log" 2>&1
grep '^PROBE_COUNT .* failures 0 ' "$w/visual_probe.log"
! grep -E 'ERROR|WARNING|FAIL' "$w/visual_probe.log"
