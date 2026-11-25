#!/bin/bash
# Requires new explicit functional lease, not used by source preparation.
set -euo pipefail
w=$(realpath "$1")
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test ! -e "$w/capture.log"
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" HVN_OUT="$w" timeout 90s godot --headless --fixed-fps 60 --path "$w/project" --script res://tests/paid_carry_capture.gd > "$w/capture.log" 2>&1
grep -E '^CAPTURE_COUNT .* failures 0 ' "$w/capture.log"
! grep -E 'ERROR|WARNING|FAIL' "$w/capture.log"
