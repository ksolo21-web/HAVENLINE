#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
test "$#" = 1 && test "$1" = --sole-functional-lease
exec 9<>/tmp/havenline-godot-headless.lock
flock -n 9
! ps -u "$(id -u)" -o comm= | grep -qiE '^(godot|blender)'
engine=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
test -x "$engine"
sha256sum -c --status SHA256SUMS
umask 077
work=$(mktemp -d /tmp/hvn-owner-33035-donor-probe.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
out=$(mktemp -d "$PWD/evidence.XXXXXXXX")
cp -a input "$work/project"
mkdir "$work"/{home,config,cache,data,state,runtime,tmp}
invoke(){
 local name=$1; shift
 timeout 45 env -i PATH="$PATH" HOME="$work/home" XDG_CONFIG_HOME="$work/config" XDG_CACHE_HOME="$work/cache" XDG_DATA_HOME="$work/data" XDG_STATE_HOME="$work/state" XDG_RUNTIME_DIR="$work/runtime" TMPDIR="$work/tmp" HVN_OWNER_GATE_EVIDENCE="$out" "$engine" --headless --path "$work/project" --audio-driver Dummy "$@" > "$out/$name.log" 2>&1
 grep -q '^Godot Engine v4\.7\.2\.stable\.official\.' "$out/$name.log"
}
invoke import --editor --import --quit
for name in GateLeaf GateLeaf_Right ThresholdPost ThresholdPost_Right; do
  grep -Fxq 'force_disable_mesh_compression=true' "$work/project/donors/$name.obj.import"
done
invoke read --script res://probe.gd
! grep -E 'ERROR:|WARNING:|Parse Error|OWNER_GATE_IMPORT_REJECT' "$out"/{import,read}.log
test "$(grep -c '^OWNER_GATE_IMPORT_OBSERVED ' "$out/read.log")" = 4
grep '^OWNER_GATE_IMPORT_OBSERVED ' "$out/read.log" | cut -d' ' -f2- > "$out/result.jsonl"
OPENBLAS_NUM_THREADS=1 python3 validate.py "$out" > "$out/strict-census.json.tmp"
mv -- "$out/strict-census.json.tmp" "$out/strict-census.json"
printf '%s\n' "$out"
