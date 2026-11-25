#!/usr/bin/env bash
set -euo pipefail
pinned=11c14a1c41971067c7dc97db69375f720a408f68
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(realpath -- "${1:?exact checkout repository}")
out=$(realpath -- "${2:?existing empty output folder}")
lease="${3:?shared native lease path}"
test -f "$lease"
test -d "$out" && test -z "$(ls -A -- "$out")"
(cd -- "$here" && sha256sum -c SHA256SUMS)
exec 9<>"$lease"
flock -n 9
if ps -u "$(id -u)" -o comm= | grep -iE '^(godot.*|Xorg|Xwayland|Xvfb|weston)$'; then echo 'competing engine or renderer' >&2; exit 1; fi
test "$(git -C "$repo" rev-parse "$pinned:HavenlineLevel1")" = d764a05246cbff96983aa27af17e2e919a946ae0
w=$(mktemp -d /tmp/hvn-l1-prepay.XXXXXXXX)
trap 'rm -rf -- "$w"' EXIT
mkdir -m700 "$w"/{home,config,data,cache,state,runtime,tmp}
export HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_DATA_HOME="$w/data" XDG_CACHE_HOME="$w/cache" XDG_STATE_HOME="$w/state" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp"
unset DISPLAY WAYLAND_DISPLAY
git -C "$repo" archive "$pinned" HavenlineLevel1 | tar -xf - -C "$w"
p="$w/HavenlineLevel1"
test ! -e "$p/tests/test_prepayment_field.gd" && test ! -e "$p/.godot"
cp -- "$here/test_prepayment_field.gd" "$p/tests/"
python3 -B "$here/verify_exact_checkout.py" "$w" > "$out/source-before.txt"
cat "$p"/assets/studio/parts/hearth_trial_02.part0{0,1,2} > "$p/assets/studio/hearth_trial_02.glb"
printf '%s  %s\n' 35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a "$p/assets/studio/hearth_trial_02.glb" | sha256sum --check --status
godot --version > "$out/engine.txt"
run() {
  local name=$1 rc=0; shift
  timeout 150 godot --headless --path "$p" "$@" > "$out/$name.log" 2>&1 || rc=$?
  grep -inE '^(WARNING|ERROR|SCRIPT ERROR|FAIL)[ :]|Parse Error|Failed (loading|to load)|Could not load' "$out/$name.log" > "$out/$name.scan" || test "$?" -eq 1
  printf '%s exit=%d diagnostic_count=%d\n' "$name" "$rc" "$(wc -l < "$out/$name.scan")" | tee -a "$out/status"
  test "$rc" -eq 0 || return 1
  if test "$name" = import; then
    sed 's/^[0-9]*://' "$out/import.scan" | LC_ALL=C sort > "$out/import-warnings-observed.txt"
    cmp "$out/import-warnings-observed.txt" "$here/import-warnings-author-expected.txt"
  else
    test ! -s "$out/$name.scan"
  fi
}
rc=0
run import --editor --import && run prepayment --script res://tests/test_prepayment_field.gd || rc=$?
python3 -B "$here/verify_exact_checkout.py" "$w" > "$out/source-after.txt"
cmp "$out/source-before.txt" "$out/source-after.txt"
find "$w" \( -name opening-v3.json -o -name opening-v3.stage \) -print > "$out/save-artifacts.txt"
test ! -s "$out/save-artifacts.txt"
exit "$rc"
