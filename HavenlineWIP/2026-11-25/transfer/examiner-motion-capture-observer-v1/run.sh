#!/bin/bash
set -euo pipefail
d="$(cd "$(dirname "$0")";pwd)"
s="$(realpath "$1")"; a="$(realpath "$2")"; w="$(realpath "$3")"
test -d "$s/.godot" && test -z "$(ls -A "$w")" && test "$(stat -c %a "$w")" = "700"
case "$w" in /tmp/hvn-motion-data.*) ;; *) exit 64;; esac
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w/runtime"
python "$d/prepare.py" "$s" "$a" "$w/capture.gd"
umask 077
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" HVN_EXAMINER_FIXTURE_MODE=B timeout 140s godot --headless --fixed-fps 60 --path "$s" --script "$w/capture.gd" >"$w/native.private.log" 2>&1
python "$d/verify_capture.py" "$w/native.private.log" >"$w/sanitized.summary.json"
cat "$w/sanitized.summary.json"
