#!/usr/bin/env bash
set -eu -o pipefail
d="$(cd -- "$(dirname -- "$0")" && pwd)"
if [[ $# -ne 7 ]]; then
  echo "usage: bash run.sh pinned-repo donor-dir prior-test.gd prior-observer.gd prior-CPU-audit.gd native-lock empty-output-dir" >&2; exit 2
fi
repo=$(realpath "$1")
donor=$(realpath "$2")
prior=$(realpath "$3")
observer=$(realpath "$4")
cpu=$(realpath "$5")
lock=$(realpath "$6")
out=$(realpath "$7")
test -f "$lock"
test -d "$out" && test -z "$(find "$out" -mindepth 1 -print -quit)"
exec 9<>"$lock"; flock -n 9 || { echo "native functional lease already held" >&2; exit 3; }
! ps -u "$(id -u)" -o comm= | grep -iq '^godot'
ref=11c14a1c41971067c7dc97db69375f720a408f68
tree=d764a05246cbff96983aa27af17e2e919a946ae0
hashcheck() { test "$(sha256sum "$1" | cut -d' ' -f1)" = "$2"; }
test "$(git -C "$repo" rev-parse "$ref:HavenlineLevel1")" = "$tree"
hashcheck "$donor/SHA256SUMS" 46f4c8450016c69d21330ba6aaea138ed8ab1fa6360c0c1bf80ca7c6cd81f2d6
hashcheck "$prior" 055641f98fb83e24072c69b7f7aa2b3d57ffdf195960b5e040ebf1e3c4f8f3cd
hashcheck "$observer" e050fbb6281310fa8b35ad68e3d9447ea365b9ad835ab4bbd69eff963d73fa97
hashcheck "$cpu" 4e7ec30240ce0f42cc9e9c1789a15bea7691ed6265e8b358b1d4e28b2cb124a7
umask 077
w=$(mktemp -d "${TMPDIR:-/tmp}/hvn-stop-guard.XXXXXX")
trap 'rm -rf -- "$w"' EXIT
mkdir -m700 "$w"/{project,home,config,data,cache,state,tmp}
p="$w/project"
git -C "$repo" archive "$ref:HavenlineLevel1" | tar -xf - -C "$p"
test ! -e "$p/.godot" && test -z "$(find "$p" -type l -print -quit)"
mkdir "$p/tests/docked_exact"
(cd "$donor"; sha256sum -c SHA256SUMS) > "$out/donor.before"
cp "$donor"/{service_counter.glb,north_counter_donor.tscn,gate_post.obj,boundary_v2.mtl} "$p/tests/docked_exact/"
cp "$prior" "$p/tests/test_docked.gd"
cp "$observer" "$p/tests/_observe_docked.gd"
cp "$cpu" "$p/tests/_audit_cpu_surface.gd"
cp "$d/prism_probe.gd" "$p/tests/_prism_probe.gd"
cp "$d/contour.json" "$p/tests/_proposal_contour.json"
export HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_STATE_HOME="$w/state" TMPDIR="$w/tmp"
export HVN_DOCKED_ROUTE_ONLY=1 HVN_DOCKED_STILLS="$out"
{ printf '%s\n' "$ref" "$tree"; (cd "$d"; sha256sum prism_probe.gd contour.json); godot --version; } > "$out/provenance.txt"
python3 "$p/tools/hydrate_assets.py" > "$out/hydrate.log"
(cd "$p"; find . -type f -not -path './.godot/*' -print0 | sort -z | xargs -0 sha256sum) > "$out/materialized.before"
timeout 160 godot --headless --path "$p" --editor --import > "$out/import.log" 2>&1
if grep -iE '^(ERROR|SCRIPT ERROR):|Parse Error|Failed (loading|to load)' "$out/import.log" > "$out/import.errors"; then exit 4; fi
status=0
timeout 180 godot --headless --path "$p" --audio-driver Dummy --script res://tests/_prism_probe.gd > "$out/route.log" 2>&1 || status=$?
find "$w" \( -name opening-v3.json -o -name opening-v3.stage \) -print > "$out/save-artifacts.txt"
test ! -s "$out/save-artifacts.txt"
(cd "$p"; sha256sum -c --quiet "$out/materialized.before") > "$out/materialized.after"
(cd "$donor"; sha256sum -c SHA256SUMS) > "$out/donor.after"
cmp "$out/donor.before" "$out/donor.after"
printf '%s\n' "$status" > "$out/godot-status.txt"
grep -E '^DOCKED_CENTER_ROUTE_RESULT checks=[0-9]+ failures=0' "$out/route.log"
test "$status" -eq 0
test "$(grep -c '^PRISM_CPU ' "$out/route.log")" -eq 16
