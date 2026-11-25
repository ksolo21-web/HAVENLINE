#!/bin/bash
set -euo pipefail
d="$(cd "$(dirname "$0")"; pwd)"
p="$(realpath "$1")"; w="$(realpath "$2")"
test -d "$p/.godot"; test -z "$(ls -A "$w")"
test ! -e "$w/bridge.gd" && test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
mkdir -p "$w/A"/{home,config,cache,data,runtime,tmp} "$w/B"/{home,config,cache,data,runtime,tmp}
chmod 700 "$w"/{A,B}/runtime
python "$d/prepare.py" "$p" "$w/bridge.gd"
run_native() {
 local k="$1" x="$w/$1"
 HOME="$x/home" XDG_CONFIG_HOME="$x/config" XDG_CACHE_HOME="$x/cache" XDG_DATA_HOME="$x/data" XDG_RUNTIME_DIR="$x/runtime" TMPDIR="$x/tmp" HVN_EXAMINER_FIXTURE_MODE="$k" timeout 100s godot --headless --fixed-fps 60 --path "$p" --script "$w/bridge.gd" >"$x/native.log" 2>&1
}
a=0; run_native A || a=$?
echo "$a" > "$w/A/status"
test "$a" = 1 || exit 16
python "$d/compare.py" --require-a "$w/A/native.log"
# No replay or capture file is supplied to B, which reacquires all inputs.
b=0; run_native B || b=$?
echo "$b" > "$w/B/status"
test "$b" = 0 || exit 17
python "$d/compare.py" "$w/A/native.log" "$w/B/native.log" > "$w/result.json"
cat "$w/result.json"
