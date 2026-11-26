#!/usr/bin/env bash
set -euo pipefail
test "${1:-}" = --sole-renderer-lease
here=$(cd -- "$(dirname "$0")" && pwd -P)
test $# -eq 2
test -t 0 || { echo "No native desktop tty." >&2; exit 20; }
test -n "${DISPLAY:-}" || { echo "No inherited X11 display." >&2; exit 20; }
lock=$(realpath -e -- "$2")
test -f "$lock" && test "$(basename "$lock")" = desktop-render.lock
test "$lock" = "$(realpath -e "$here/../hvn-native-visual-smoke-leasefix-v1/desktop-render.lock")"
exec 9<>"$lock"
flock -n 9
! ps -u "$(id -u)" -o comm= | grep -qiE '^(godot|blender)'
engine=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
test -x "$engine"
(cd "$here"; sha256sum -c --status SHA256SUMS)
(cd "$here/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
umask 077
out=$(mktemp -d "$here/graphics-evidence.XXXXXXXX")
w=$(mktemp -d /tmp/hvn-l1-r17-normal-draw.XXXXXXXX)
profile=""
clean(){ rm -rf -- "$w"; [[ -z "$profile" ]] || rm -rf -- "$profile"; }
trap clean EXIT
profile=$(mktemp -d /tmp/havenline-l1-v3-l1-e2e-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
printf 'HAVENLINE-L1-E2E-ROUTE-V1\n' > "$profile/L1-E2E-ROUTE"
mark=$(stat -c '%d:%i:%a' "$profile")
cp -a "$here/staged/HavenlineLevel1" "$w/project"
(cd "$w/project"; sha256sum -c --status "$here/staged/draw-source.sha256")
allowx=()
if [[ -n "${XAUTHORITY:-}" ]]; then
  test -f "$XAUTHORITY"
  allowx+=("XAUTHORITY=$XAUTHORITY")
elif [[ -f "${HOME:-}/.Xauthority" ]]; then
  allowx+=("XAUTHORITY=$HOME/.Xauthority")
fi
exec_phase(){
  local phase=$1; shift; local iso="$w/env-$phase"
  mkdir -m700 -p "$iso"/{home,data,config,cache,state,runtime,tmp}
  timeout 180 env -i PATH="$PATH" DISPLAY="$DISPLAY" "${allowx[@]}" HOME="$iso/home" XDG_DATA_HOME="$iso/data" XDG_CACHE_HOME="$iso/cache" XDG_CONFIG_HOME="$iso/config" XDG_STATE_HOME="$iso/state" XDG_RUNTIME_DIR="$iso/runtime" TMPDIR="$iso/tmp" HVN_L1_STOCK_CAPTURE="$out"        "$engine" --path "$w/project" --audio-driver Dummy "$@" > "$out/$phase.log" 2>&1
  grep -q '^Godot Engine v4\.7\.2\.stable\.official\.' "$out/$phase.log"
}
snapshot(){
  (cd "$profile"
    find . -mindepth 1 -maxdepth 1 -printf '%y %m %P\n' | sort
    find . -mindepth 1 -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum)
}
exec_phase import --headless --editor --import --quit
obj="^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$"
test "$(grep -Ec "$obj" "$out/import.log")" -eq 18
if grep -Ei 'ERROR:|WARNING:|Parse Error' "$out/import.log" | grep -Ev "$obj"; then exit 3; fi
vsync="WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver."
for phase in write cold; do
  test "$(stat -c '%d:%i:%a' "$profile")" = "$mark"
  exec_phase "$phase" --display-driver x11 --rendering-method gl_compatibility --rendering-driver opengl3 --resolution 1280x720 --fixed-fps 60 --script res://tests/hvn_l1_combined_draw.gd -- "--l1-disposable-profile=$profile" "--hvn-l1-e2e=$phase"
  if grep -Ei 'ERROR:|WARNING:|Parse Error|^FAIL |^DRAW_REJECT ' "$out/$phase.log" | grep -Fxv "$vsync"; then exit 4; fi
  test "$(grep -Fx "$vsync" "$out/$phase.log" | wc -l || true)" -le 1
  grep -Eq '^OpenGL .* - Compatibility - Using Device: Mesa - llvmpipe ' "$out/$phase.log"
  if [[ "$phase" == write ]]; then
    grep -Fxq 'L1_COMBINED_ROUTE phase=write checks=57 failures=0' "$out/$phase.log"
    grep -Fxq 'L1_STOCK_POST_DRAW_OK write 5' "$out/$phase.log"
    test -f "$profile/opening-v3.json"
    test ! -e "$profile/opening-v3.stage"
    test -z "$(find "$profile" -mindepth 1 -maxdepth 1 ! -type f -print -quit)"
    test "$(find "$profile" -mindepth 1 -maxdepth 1 -type f | wc -l)" = 3
    snapshot > "$out/disposable.before"
    python3 "$here/summarize.py" --validate-live-disposable "$profile" > "$out/writer-digest.json"
  else
    grep -Fxq 'L1_COMBINED_ROUTE phase=cold checks=10 failures=0' "$out/$phase.log"
    grep -Fxq 'L1_STOCK_POST_DRAW_OK cold 1' "$out/$phase.log"
    snapshot > "$out/disposable.after"
    cmp "$out/disposable.before" "$out/disposable.after"
  fi
done
test "$(stat -c '%d:%i:%a' "$profile")" = "$mark"
test -z "$(find "$w" -type f -name 'opening-v3.*' -print -quit)"
(cd "$w/project"; sha256sum -c --status "$here/staged/draw-source.sha256")
(cd "$here/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
# The headless replay verifier permits zero runtime warnings. Give it an
# exact byte view where only the already separately checked X11 advisory is
# removed; preserve the raw desktop log digests independently in frame evidence.
view="$w/verified-functional-view"
mkdir "$view"
cp "$out"/{import.log,disposable.before,disposable.after,writer-digest.json} "$view/"
for phase in write cold; do
  grep -Fxv "$vsync" "$out/$phase.log" > "$view/$phase.log"
done
python3 "$here/summarize.py" "$view" > "$view/functional.json"
python3 - "$view/functional.json" > "$out/functional.json" <<'PY_SCOPE'
import json,sys
with open(sys.argv[1]) as f: r=json.load(f)
r["scope"]="same two-process exact detached route with explicit R17 visual-only scene in graphical software X11; ordinary handler inputs only, not OS/phone/framerate proof"
r["log_digest_scope"]="functional view removes only the exact separately validated X11 driver advisory; raw desktop log hashes in frame-evidence.json"
print(json.dumps(r,sort_keys=True,indent=2))
PY_SCOPE
python3 "$here/validate_draw.py" "$out" > "$out/frame-evidence.json"
python3 "$here/validate_r17.py" "$out" "$here/stock-result.json" > "$out/r17-evidence.json"
python3 "$here/verify_normal_delta.py" "$out/frame-evidence.json" "$here/original-frame-evidence.json" > "$out/normal-frame-delta.json"
printf '%s\n' "$out"
