#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_glb="${1:?Pass original pinned Character1.glb}"
lock="${2:?Pass shared existing tool lock}"
test -f "$lock"
exec 9<>"$lock"
flock -n 9 || { echo 'Godot lease in use' >&2; exit 1; }
if pgrep -x godot >/dev/null; then echo 'A competing Godot process exists' >&2; exit 1; fi
scratch="$(mktemp -d "${TMPDIR:-/tmp}/hvn-c1-stock-socket.XXXXXXXX")"
trap 'rm -rf "$scratch"' EXIT
mkdir "$scratch/"{project,home,config,cache,data,state,tmp,runtime}
chmod 700 "$scratch/runtime"
cp "$here/"{project.godot,socket_stock.gd} "$scratch/project/"
cp "$source_glb" "$scratch/project/source.input"
printf '%s  %s\n' '95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099' "$scratch/project/source.input" | sha256sum --check --status
env HOME="$scratch/home" XDG_CONFIG_HOME="$scratch/config" XDG_CACHE_HOME="$scratch/cache" XDG_DATA_HOME="$scratch/data" XDG_STATE_HOME="$scratch/state" XDG_RUNTIME_DIR="$scratch/runtime" TMPDIR="$scratch/tmp" timeout 25 godot --headless --path "$scratch/project" --script res://socket_stock.gd
