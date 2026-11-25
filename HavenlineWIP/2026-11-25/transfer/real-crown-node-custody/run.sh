#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_glb="${1:?Provide the pinned Level 1 starter ground GLB}"
lock="${2:?Provide existing Havenline Godot headless lock path}"
test -f "$lock"
exec 9<>"$lock"
flock -n 9 || { echo 'Godot lease in use' >&2; exit 1; }
if pgrep -x godot >/dev/null; then echo 'A competing Godot process exists' >&2; exit 1; fi
scratch="$(mktemp -d "${TMPDIR:-/tmp}/hvn-crown-custody.XXXXXXXX")"
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/"{project,home,config,cache,data,state,tmp,runtime}
chmod 700 "$scratch/runtime"
cp "$here/"{project.godot,planner_upstream.gd,test.gd} "$scratch/project/"
cp "$source_glb" "$scratch/project/source.input"
printf '%s  %s\n' '0ae04e267c01a0163cc29f6eabb23c1d8cc93edb635ced9e865a5452dcde9151' "$scratch/project/planner_upstream.gd" '31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554' "$scratch/project/source.input" | sha256sum --check --status
env HOME="$scratch/home" XDG_CONFIG_HOME="$scratch/config" XDG_CACHE_HOME="$scratch/cache" XDG_DATA_HOME="$scratch/data" XDG_STATE_HOME="$scratch/state" XDG_RUNTIME_DIR="$scratch/runtime" TMPDIR="$scratch/tmp" timeout 25 godot --headless --path "$scratch/project" --script res://test.gd
