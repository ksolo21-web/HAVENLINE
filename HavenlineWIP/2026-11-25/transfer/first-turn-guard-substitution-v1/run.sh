#!/bin/bash
set -euo pipefail
d="$(cd "$(dirname "$0")"; pwd)"
p="$(realpath "$1")"; w="$(realpath "$2")"
test -d "$p/.godot"; test -z "$(ls -A "$w")"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
mkdir -p "$w"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w/runtime"
python "$d/prepare.py" "$p" "$w/examiner.gd"
HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" HVN_EXAMINER_FIXTURE_MODE=B timeout 140s godot --headless --fixed-fps 60 --path "$p" --script "$w/examiner.gd" >"$w/native.log" 2>&1
test "$(grep -c '^EXAM_FIRST_MID_SUPPORT ' "$w/native.log")" = 1
test "$(grep -c '^EXAM_QUALIFIED ' "$w/native.log")" = 1
! grep -Eq '^(ERROR|WARNING|SCRIPT ERROR|FATAL|EXAM_HOLD|FAIL )' "$w/native.log"
grep '^EXAM_QUALIFIED ' "$w/native.log"
