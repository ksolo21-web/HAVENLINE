#!/usr/bin/env bash
set -eu -o pipefail
D=$(cd "$(dirname "$0")" && pwd)
repo=$(realpath "$1"); out=$(realpath "$2")
test -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}"
test -d "$out" && test -z "$(find "$out" -mindepth 1 -print -quit)"
lock=$(realpath "$3")
test -f "$lock"
exec 9<>"$lock"; flock -n 9
! ps -u "$(id -u)" -o comm= | grep -iq '^godot'
ref=11c14a1c41971067c7dc97db69375f720a408f68
tree=d764a05246cbff96983aa27af17e2e919a946ae0
donor="$D/.."
critic="$D/../verification"
test "$(git -C "$repo" rev-parse "$ref:HavenlineLevel1")" = "$tree"
test "$(sha256sum "$donor/SHA256SUMS" | cut -d' ' -f1)" = 46f4c8450016c69d21330ba6aaea138ed8ab1fa6360c0c1bf80ca7c6cd81f2d6
test "$(sha256sum "$critic/test_docked.gd" | cut -d' ' -f1)" = 055641f98fb83e24072c69b7f7aa2b3d57ffdf195960b5e040ebf1e3c4f8f3cd
umask 077
w=$(mktemp -d "${TMPDIR:-/tmp}/hvn-docked-render.XXXXXX"); trap 'rm -rf -- "$w"' EXIT
mkdir -m700 "$w"/{project,home,config,data,cache,state,tmp}
p="$w/project"
git -C "$repo" archive "$ref:HavenlineLevel1" | tar -xf - -C "$p"
test ! -e "$p/.godot" && test -z "$(find "$p" -type l -print -quit)"
mkdir "$p/tests/docked_exact"
(cd "$donor"; sha256sum -c SHA256SUMS) > "$out/donor.before"
cp "$donor"/{service_counter.glb,north_counter_donor.tscn,gate_post.obj,boundary_v2.mtl} "$p/tests/docked_exact/"
cp "$critic/test_docked.gd" "$p/tests/"
cp "$D/observe.gd" "$p/tests/_observe_docked.gd"
export HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_STATE_HOME="$w/state" TMPDIR="$w/tmp" HVN_DOCKED_STILLS="$out"
# Runner must provide a sanctioned disposable display/runtime; no connection to owner desktop.
{ printf '%s\n' "$ref" "$tree"; sha256sum "$D/observe.gd"; godot --version; } > "$out/provenance.txt"
python3 "$p/tools/hydrate_assets.py" > "$out/hydrate.log"
(cd "$p"; find . -type f -not -path './.godot/*' -print0 | sort -z | xargs -0 sha256sum) > "$out/materialized.before"
timeout 150 godot --headless --path "$p" --editor --import > "$out/import.log" 2>&1
if grep -iE '^(ERROR|SCRIPT ERROR):|Parse Error|Failed (loading|to load)' "$out/import.log" > "$out/import.errors"; then exit 2; fi
timeout 180 godot --path "$p" --audio-driver Dummy --resolution 1280x720 --script res://tests/_observe_docked.gd > "$out/render.log" 2>&1
grep -E '^DOCKED_RENDER_RESULT checks=[0-9]+ failures=0$' "$out/render.log"
test "$(grep -c '^NATIVE_SHOT ' "$out/render.log")" -eq 16
test "$(grep -c '^COUNTER_CENTER ' "$out/render.log")" -eq 4
if grep -iE '^(ERROR|SCRIPT ERROR|FAIL)[ :]|Parse Error|Failed (loading|to load)' "$out/render.log" > "$out/render.errors"; then exit 3; fi
find "$w" \( -name opening-v3.json -o -name opening-v3.stage \) -print > "$out/save-artifacts.txt"
test ! -s "$out/save-artifacts.txt"
(cd "$p"; sha256sum -c "$out/materialized.before") > "$out/materialized.after"
(cd "$donor"; sha256sum -c SHA256SUMS) > "$out/donor.after"
cmp "$out/donor.before" "$out/donor.after"
