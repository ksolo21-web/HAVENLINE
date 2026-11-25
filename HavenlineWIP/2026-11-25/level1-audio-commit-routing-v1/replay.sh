#!/bin/bash
# Only execute after coordinator grants exact serial headless functional lease.
set -euo pipefail
repo="$(realpath "$1")"
cd "$(dirname "$0")"
self="$PWD"
sha=11c14a1c41971067c7dc97db69375f720a408f68
check() { test "$(git -C "$repo" rev-parse "$sha:HavenlineLevel1/$1")" = "$2"; }
check previews/integrated_opening.tscn 39180754353c4f73355f253dc4d9cb7e1427d1c1
check previews/integrated_opening.gd cc54fb10b5270f513baa2c3743d4879e29ebb41a
check opening.gd 8de9499b0a48d920516d3b07c889cfb8a0808038
check opening_ledger.gd 873def40c950279b210e2b2d0bed5d85625ea189
check opening_save.gd 7ba67c0919048ee1c7396a6ef42cb8ec5de99d24
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9 || exit 75
p="$(mktemp -d "$self/fixture-owned.XXXXXXXX")"
trap 'rm -rf -- "$p"' EXIT
out="$(mktemp -d "$self/runtime.XXXXXXXX")"
export HOME="$p/home" XDG_DATA_HOME="$p/data" XDG_CONFIG_HOME="$p/config" XDG_CACHE_HOME="$p/cache" XDG_RUNTIME_DIR="$p/run" TMPDIR="$p/tmp"
mkdir -m700 "$HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" "$TMPDIR"
git -C "$repo" archive "$sha" HavenlineLevel1 | tar -x -C "$p"
project="$p/HavenlineLevel1"
studio="$project/assets/studio"
cat "$studio"/parts/hearth_trial_02.part{00,01,02} > "$studio/hearth_trial_02.glb"
printf "35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a  %s\n" "$studio/hearth_trial_02.glb" | sha256sum --check --status
cp sfx_observer.gd test_sfx_route.gd "$project/tests/"
run(){
   local name="$1"; shift
   timeout 120 "${GODOT:-godot}" --headless --audio-driver Dummy --path "$project" "$@" > "$out/$name.log" 2>&1 || { tail -50 "$out/$name.log" >&2; return 1; }
   if grep -Eq '(SCRIPT ERROR|^ERROR:|Parse Error)' "$out/$name.log"; then tail -50 "$out/$name.log" >&2; return 1; fi
}
run import --editor --import
# The preserved existing disposable save code admits only marked paths under /tmp.
profiles=()
cleanup() { rm -rf -- "$p" "${profiles[@]}"; }
trap cleanup EXIT
for phase in write cold savefail mute; do
   if [ "$phase" != cold ]; then
      profile="$(mktemp -d /tmp/havenline-l1-v3-combined-sfx-XXXXXXXX)"
      profiles+=("$profile")
      printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
      printf 'HAVENLINE-COMBINED-COLD-V1\n' > "$profile/COMBINED-COLD-FIXTURE"
   fi
   run "$phase" --script res://tests/test_sfx_route.gd -- "--l1-disposable-profile=$profile" --l1-enable-combined-cold-fixture "--sfx-phase=$phase"
   grep 'sfx-route' "$out/$phase.log"
done
printf '%s\n' "$out"
