#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:?workspace}"
qa="$here"
here="$qa/../chop-input-router-v1"
(cd "$here"; sha256sum -c SHA256SUMS)
repo="${2:?base repository}"
out="${3:?new evidence dir}"
mkdir -p "$out"; out="$(cd "$out" && pwd)"
base=11c14a1c41971067c7dc97db69375f720a408f68
test "$(git -C "$repo" rev-parse "$base:HavenlineLevel1")" = d764a05246cbff96983aa27af17e2e919a946ae0
orig="$qa/../chop-impact-retirement-v1"
test "$(sha256sum "$orig/SHA256SUMS" | cut -d' ' -f1)" = d96d0a48788c49915691f3275eb9860565f19a7d7b4b39894d29254393b7dbec
(cd "$orig"; sha256sum -c SHA256SUMS >/dev/null)
test "$(sha256sum "$here/tests/overlay.py" | cut -d' ' -f1)" = 42cdfad4d69d5f8ac7d2e5ff62902009106d467e6b3c9aefe95338bf8ea50310
test "$(sha256sum "$here/tests/test_router.gd" | cut -d' ' -f1)" = d605d66635b5f41c64a998c05777005c68c4882f3f672a0c84111a66d93f2442
test "$(sha256sum "$here/source/chop_input_router.gd" | cut -d' ' -f1)" = 6fb0d61b6f9db7be1c7f5f878687a509fc7165a5484015686fd4c8b2212c53b0
test "$(sha256sum "$orig/source/chop_impact_bridge.gd" | cut -d' ' -f1)" = 010c29f59690306a6ea4edf5846aaa540397556972c4591ad2c2be7d414e8388
tmp="$(mktemp -d /tmp/hvn-chop-router.XXXXXX)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp"/{p,home,config,data,cache,state,runtime,t}
chmod 700 "$tmp/runtime"
git -C "$repo" archive "$base" HavenlineLevel1 | tar xf - --strip-components=1 -C "$tmp/p"
python "$tmp/p/tools/hydrate_assets.py" > "$out/hydrate.log"
cp "$orig/source/chop_impact_bridge.gd" "$here/source/chop_input_router.gd" "$here/tests/test_router.gd" "$tmp/p/"
cp "$qa/focus.gd" "$tmp/p/"
cp "$tmp/p/opening.gd" "$tmp/original.gd"
python "$here/tests/overlay.py" "$tmp/p/opening.gd"
diff -u --label original-opening.gd --label test-only-opening.gd "$tmp/original.gd" "$tmp/p/opening.gd" > "$out/test-only.diff" || test "$?" -eq 1
export HOME="$tmp/home" XDG_CONFIG_HOME="$tmp/config" XDG_DATA_HOME="$tmp/data" XDG_CACHE_HOME="$tmp/cache" XDG_STATE_HOME="$tmp/state" XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp/t"
(
 flock -n 8 || exit 75
 flock -n 9 || exit 75
 if ps -eo comm | grep -iE '^(godot.*|Xorg|Xwayland|Xvfb|weston)$'; then exit 76; fi
 timeout 90s godot --headless --path "$tmp/p" --editor --import > "$out/import.log" 2>&1
 grep -E '^(ERROR|SCRIPT ERROR):|Parse Error' "$out/import.log" && exit 77
 timeout 60s godot --headless --path "$tmp/p" --script res://focus.gd > "$out/focus.log" 2>&1
 ! grep -E '^(ERROR|SCRIPT ERROR|FAIL)[ :]|Parse Error' "$out/focus.log"
 find "$tmp" \( -name opening-v3.json -o -name opening-v3.stage \) > "$out/save-artifacts.txt"
 test ! -s "$out/save-artifacts.txt"
) 8<>"$root/.havenline-renderer.lock" 9<>/tmp/havenline-godot-headless.lock
