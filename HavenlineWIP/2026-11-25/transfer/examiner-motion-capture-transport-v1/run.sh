#!/bin/bash
set -euo pipefail
d="$(cd "$(dirname "$0")";pwd)"
s="$(realpath "$1")"; a="$(realpath "$2")"; w="$(realpath "$3")"
test -d "$s/.godot" && test -z "$(ls -A "$w")" && test "$(stat -c %a "$w")" = "700"
case "$w" in /workspace/*/hvn-motion-private.*|/workspace/*/*/hvn-motion-private.*) ;; *) exit 64;; esac
test "$(stat -c %d "$w")" != "$(stat -c %d /tmp)"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
umask 077
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
printf %s "HAVENLINE EXACT CAPTURE ONLY v1" > "$w/capture.owner"
python "$d/prepare.py" "$s" "$a" "$w/capture.gd"
set +e
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" HVN_EXAMINER_FIXTURE_MODE=B HVN_EXAM_CAPTURE_FILE="$w/motion.private.ndjson" timeout 140s godot --headless --fixed-fps 60 --path "$s" --script "$w/capture.gd" >"$w/native.core.log" 2>&1
r=$?
set -e
printf '%s\n' "$r" >"$w/native.status"
test "$r" = 0
test "$(stat -c %s "$w/native.core.log")" -lt 65536
test "$(stat -c %s "$w/motion.private.ndjson")" -lt 4194304
test "$(wc -l < "$w/motion.private.ndjson")" = 135
cat "$w/native.core.log" "$w/motion.private.ndjson" >"$w/whole.private.log"
python "$d/../hvn-l1-examiner-motion-capture-observer-v1/verify_capture.py" "$w/whole.private.log" >"$w/sanitized.summary.json"
cat "$w/sanitized.summary.json"
