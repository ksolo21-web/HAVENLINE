#!/usr/bin/env bash
set -euo pipefail
self="$(cd "$(dirname "$0")/.." && pwd)"
archive="$(dirname "$self")"
root="${1:?common lock workspace}"
r="${2:?checkout with pinned base}"
out="${3:?new empty output directory}"
mkdir -p "$out"; test -z "$(find "$out" -mindepth 1 -print -quit)"
old="$archive/chop-input-router-v1"
qa="$archive/chop-focus-qa-v1"
impact="$archive/chop-impact-retirement-v1"
test "$(sha256sum "$old/source/chop_input_router.gd" | cut -d' ' -f1)" = 6fb0d61b6f9db7be1c7f5f878687a509fc7165a5484015686fd4c8b2212c53b0
test "$(sha256sum "$old/tests/test_router.gd" | cut -d' ' -f1)" = d605d66635b5f41c64a998c05777005c68c4882f3f672a0c84111a66d93f2442
test "$(sha256sum "$old/tests/overlay.py" | cut -d' ' -f1)" = 42cdfad4d69d5f8ac7d2e5ff62902009106d467e6b3c9aefe95338bf8ea50310
test "$(sha256sum "$qa/focus.gd" | cut -d' ' -f1)" = 962cbe98f2d9360db4982b8e084364a33236ea5afa6840b5cf7f2eb932fa27d3
test "$(sha256sum "$impact/source/chop_impact_bridge.gd" | cut -d' ' -f1)" = 010c29f59690306a6ea4edf5846aaa540397556972c4591ad2c2be7d414e8388
test "$(sha256sum "$impact/tests/test_chop_impact.gd" | cut -d' ' -f1)" = 4f2c247855f29e7e3ce872d8daa90ab35b691beb761f82f1df62f64433fbaf6c
test "$(sha256sum "$impact/tests/test_retirement.gd" | cut -d' ' -f1)" = 503c73547c13d92136517a0c1dd3e8683bbe60abc687126a8b738aca3a6c2821
base=11c14a1c41971067c7dc97db69375f720a408f68
test "$(git -C "$r" rev-parse "$base:HavenlineLevel1")" = d764a05246cbff96983aa27af17e2e919a946ae0
d="$(mktemp -d "${TMPDIR:-/tmp}/hvn-focus-repair.XXXXXX")"
trap 'rm -rf -- "$d"' EXIT
mkdir "$d/p"
git -C "$r" archive "$base" HavenlineLevel1 |tar xf - --strip-components=1 -C "$d/p"
p="$d/p"
python3 "$p/tools/hydrate_assets.py" > "$out/hydrate.log"
cp "$p/opening.gd" "$d/orig.gd"
cp "$old/source/chop_input_router.gd" "$old/tests/test_router.gd" "$qa/focus.gd" "$impact/source/chop_impact_bridge.gd" "$impact/tests/"test_*.gd "$self/tests/focus_fixed.gd" "$p/"
python3 "$old/tests/overlay.py" "$p/opening.gd"
run () {
 local n="$1"; shift
 mkdir -p "$d/$n"/{home,config,data,cache,state,runtime,tmp}
 chmod 700 "$d/$n/runtime"
 env HOME="$d/$n/home" XDG_CONFIG_HOME="$d/$n/config" XDG_DATA_HOME="$d/$n/data" XDG_CACHE_HOME="$d/$n/cache" XDG_STATE_HOME="$d/$n/state" XDG_RUNTIME_DIR="$d/$n/runtime" TMPDIR="$d/$n/tmp" timeout 95s godot --headless --path "$p" "$@" >"$out/$n.log" 2>&1
}
(
 flock -n 8 || exit 75
 flock -n 9 || exit 75
 if ps -eo comm | grep -iE '^(godot.*|Xorg|Xwayland|Xvfb|weston)$'; then exit 76; fi
 run import --editor --import --quit
 run old_focus --script res://focus.gd
 grep -Fx 'FOCUS_RESULT exposures=3 checks=18 failures=0' "$out/old_focus.log"
 cp "$self/source/chop_input_router.gd" "$p/"
 cp "$d/orig.gd" "$p/opening.gd"
 python3 "$self/tests/overlay.py" "$p/opening.gd" --focus
 diff -u --label pinned-opening.gd "$d/orig.gd" --label disposable-opening.gd "$p/opening.gd" >"$out/test-only.diff" || test "$?" = 1
 for t in focus_fixed test_router test_chop_impact test_retirement; do run "$t" --script "res://$t.gd"; done
 ! grep -E '^(ERROR|SCRIPT ERROR|FAIL)[ :]|Parse Error' "$out/"*.log
 find "$d" \( -name opening-v3.json -o -name opening-v3.stage \) >"$out/save-artifacts.txt"
 test ! -s "$out/save-artifacts.txt"
) 8<>"$root/.havenline-renderer.lock" 9<>/tmp/havenline-godot-headless.lock
