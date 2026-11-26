#!/usr/bin/env bash
set -euo pipefail
test "${1:-}" = --root-granted-functional-lease
here=$(cd -- "$(dirname "$0")" && pwd -P)
engine=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
test -x "$engine"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
! ps -u "$(id -u)" -o comm= | grep -qiE '^(godot|blender)'
umask 077
out=$(mktemp -d "$here/run.XXXXXXXX")
w=$(mktemp -d /tmp/hvn-l1-e2e-run.XXXXXXXX)
profile=""
clean(){ rm -rf -- "$w"; [[ -z "$profile" ]] || rm -rf -- "$profile"; }
trap clean EXIT
profile=$(mktemp -d /tmp/havenline-l1-v3-l1-e2e-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
printf 'HAVENLINE-L1-E2E-ROUTE-V1\n' > "$profile/L1-E2E-ROUTE"
profile_id=$(stat -c '%d:%i:%a' "$profile")
(cd "$here/staged/HavenlineLevel1"; sha256sum -c --status ../final.sha256)
cp -a "$here/staged/HavenlineLevel1" "$w/project"
(cd "$w/project"; sha256sum -c --status "$here/staged/final.sha256")
run(){
  local phase=$1; shift
  local p="$w/isolated-$phase"
  mkdir -m700 -p "$p"/{home,data,config,cache,state,runtime,tmp}
  timeout 180 env HOME="$p/home" XDG_DATA_HOME="$p/data" XDG_CONFIG_HOME="$p/config" XDG_CACHE_HOME="$p/cache" XDG_STATE_HOME="$p/state" XDG_RUNTIME_DIR="$p/runtime" TMPDIR="$p/tmp" \
    "$engine" --headless --audio-driver Dummy --path "$w/project" "$@" > "$out/$phase.log" 2>&1
  grep -q '^Godot Engine v4\.7\.2\.stable\.official\.' "$out/$phase.log"
  if [[ "$phase" == import ]]; then
    local allow="^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$"
    test "$(grep -Ec "$allow" "$out/$phase.log")" -eq 18
    ! grep -Ei 'ERROR:|WARNING:|Parse Error' "$out/$phase.log" | grep -Ev "$allow"
  else
    ! grep -Ei 'ERROR:|WARNING:|Parse Error|^FAIL ' "$out/$phase.log"
  fi
}
snapshot(){
  ( cd "$profile"
    find . -mindepth 1 -maxdepth 1 -printf '%y %m %P\n' | sort
    find . -mindepth 1 -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum )
}
run import --editor --import --quit
test ! -e "$profile/opening-v3.json"
test "$(stat -c '%d:%i:%a' "$profile")" = "$profile_id"
run write --fixed-fps 60 --script res://tests/hvn_l1_combined_route.gd -- "--l1-disposable-profile=$profile" --hvn-l1-e2e=write
grep -E '^L1_COMBINED_ROUTE phase=write checks=[1-9][0-9]* failures=0$' "$out/write.log"
test -f "$profile/opening-v3.json"
test ! -e "$profile/opening-v3.stage"
test "$(find "$profile" -mindepth 1 -maxdepth 1 -type f | wc -l)" -eq 3
test -z "$(find "$profile" -mindepth 1 -maxdepth 1 ! -type f -print -quit)"
snapshot > "$out/disposable.before"
python "$here/summarize.py" --validate-live-disposable "$profile" > "$out/writer-digest.json"
test "$(stat -c '%d:%i:%a' "$profile")" = "$profile_id"
# Distinct process and OS contexts; same exact marked copy and checkpoint bytes.
run cold --fixed-fps 60 --script res://tests/hvn_l1_combined_route.gd -- "--l1-disposable-profile=$profile" --hvn-l1-e2e=cold
grep -E '^L1_COMBINED_ROUTE phase=cold checks=[1-9][0-9]* failures=0$' "$out/cold.log"
snapshot > "$out/disposable.after"
cmp "$out/disposable.before" "$out/disposable.after"
test "$(stat -c '%d:%i:%a' "$profile")" = "$profile_id"
test "$(find "$w" -type f -name 'opening-v3.*' | wc -l)" -eq 0
(cd "$w/project"; sha256sum -c --status "$here/staged/final.sha256")
(cd "$here/staged/HavenlineLevel1"; sha256sum -c --status ../final.sha256)
python "$here/summarize.py" "$out" > "$out/result.json"
printf '%s\n' "$out"
