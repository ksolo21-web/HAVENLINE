#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
source_repo="${1:?existing checkout containing pinned source}"
lock="${2:?existing functional headless lock}"
base=11c14a1c41971067c7dc97db69375f720a408f68
test "$(git -C "$source_repo" rev-parse "$base:HavenlineLevel1")" = d764a05246cbff96983aa27af17e2e919a946ae0
test -f "$lock"
exec 9<>"$lock"
flock -n 9 || { echo 'Godot lease in use' >&2; exit 1; }
if pgrep -x godot >/dev/null; then echo 'A competing Godot process exists' >&2; exit 1; fi
scratch="$(mktemp -d /tmp/hvn-real-anchor.XXXXXXXX)"
trap 'rm -rf "$scratch"' EXIT
git -C "$source_repo" archive "$base" HavenlineLevel1 | tar -xf - -C "$scratch"
base_project="$scratch/HavenlineLevel1"
printf '%s  %s\n' '31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554' "$base_project/assets/studio/starter_ground_wood_lod.glb" | sha256sum --check --status
cat "$base_project/assets/studio/parts/hearth_trial_02.part"{00,01,02} > "$base_project/assets/studio/hearth_trial_02.glb"
printf '%s  %s\n' '35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a' "$base_project/assets/studio/hearth_trial_02.glb" | sha256sum --check --status
mkdir -p "$scratch/import-profile/"{home,config,cache,data,state,tmp,runtime}
chmod 700 "$scratch/import-profile/runtime"
profile() {
  local p="$1"; shift
  env HOME="$p/home" XDG_CONFIG_HOME="$p/config" XDG_CACHE_HOME="$p/cache" XDG_DATA_HOME="$p/data" XDG_STATE_HOME="$p/state" XDG_RUNTIME_DIR="$p/runtime" TMPDIR="$p/tmp" "$@"
}
profile "$scratch/import-profile" timeout 55 godot --headless --editor --path "$base_project" --import > "$scratch/import.log" 2>&1 || { tail -35 "$scratch/import.log"; exit 1; }
if grep -Ei 'SCRIPT ERROR:|ERROR:' "$scratch/import.log"; then exit 1; fi
cp "$here/witness.gd" "$base_project/tests/witness.gd"
mkdir -p "$scratch/test-profile/"{home,config,cache,data,state,tmp,runtime}
chmod 700 "$scratch/test-profile/runtime"
rc=0
profile "$scratch/test-profile" timeout 35 godot --headless --path "$base_project" --script res://tests/witness.gd > "$scratch/clearance.log" 2>&1 || rc=$?
if grep -Ei 'SCRIPT ERROR:|^ERROR:' "$scratch/clearance.log"; then cat "$scratch/clearance.log"; exit 2; fi
cat "$scratch/clearance.log"
if find "$scratch" \( -name 'opening-v3.json' -o -name 'opening-v3.stage' \) -print -quit | grep -q .; then exit 2; fi
exit "$rc"
