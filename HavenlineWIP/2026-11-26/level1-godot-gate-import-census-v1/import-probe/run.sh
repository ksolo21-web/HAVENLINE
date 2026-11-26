#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
test "${1:-}" = --sole-functional-lease
exec 9<>/tmp/havenline-godot-headless.lock
flock -n 9
! ps -u "$(id -u)" -o comm= | grep -qiE '^(godot|blender)'
engine=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
test -x "$engine"
sha256sum -c --status SHA256SUMS
umask 077
work=$(mktemp -d /tmp/hvn-gate-donor-probe.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
out=$(mktemp -d "$PWD/evidence.XXXXXXXX")
cp -a input "$work/project"
mkdir "$work"/{home,config,cache,data,state,runtime,tmp}
invoke(){
 local name=$1; shift
 timeout 45 env -i PATH="$PATH" HOME="$work/home" XDG_CONFIG_HOME="$work/config" XDG_CACHE_HOME="$work/cache" XDG_DATA_HOME="$work/data" XDG_STATE_HOME="$work/state" XDG_RUNTIME_DIR="$work/runtime" TMPDIR="$work/tmp" "${engine}" --headless --path "$work/project" --audio-driver Dummy "$@" > "$out/$name.log" 2>&1
}
invoke import --editor --import --quit
invoke read --script res://probe.gd
test "$(grep -c '^OBJ_IMPORT_OBSERVED ' "$out/read.log")" = 4
grep '^OBJ_IMPORT_OBSERVED ' "$out/read.log" | cut -d' ' -f2- > "$out/result.jsonl"
! grep -E 'ERROR:|WARNING:|Parse Error|OBJ_IMPORT_REJECT' "$out/read.log"
printf '%s\n' "$out"
