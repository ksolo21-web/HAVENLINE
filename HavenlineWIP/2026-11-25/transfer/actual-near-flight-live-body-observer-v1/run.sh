#!/bin/bash
set -euo pipefail
d="$(cd "$(dirname "$0")"; pwd)"
p="$(realpath "$1")"; w="$(realpath "$2")"
test -d "$p/.godot"; test -z "$(ls -A "$w")"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w/runtime"
python "$d/prepare.py" "$p" "$w/examiner.gd"
rc=0
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" HVN_EXAMINER_FIXTURE_MODE=B timeout 140s godot --headless --fixed-fps 60 --path "$p" --script "$w/examiner.gd" >"$w/native.log" 2>&1 || rc=$?
echo "$rc" > "$w/exit.txt"
test "$rc" = 22
! grep -Eq '^(ERROR|WARNING|SCRIPT ERROR|FATAL|EXAM_SUPPORT_UNEXPECTED_PASS|EXAM_QUALIFIED|FAIL )' "$w/native.log"
diff <(grep -E '^EXAM_(ADMISSION_PREFIX|FLIGHT_GEOM_HOLD|HOLD) ' "$d/../hvn-l1-actual-near-flight-first-result-v1/native.log") <(grep -E '^EXAM_(ADMISSION_PREFIX|FLIGHT_GEOM_HOLD|HOLD) ' "$w/native.log")
test "$(grep -c '^EXAM_SUPPORT_INPUT ' "$w/native.log")" = 1
test "$(grep -c '^EXAM_SUPPORT_GAPS ' "$w/native.log")" = 1
grep -E '^EXAM_(SUPPORT_INPUT|SUPPORT_GAPS|ADMISSION_PREFIX|FLIGHT_GEOM_HOLD|HOLD) ' "$w/native.log" > "$d/native.txt"
