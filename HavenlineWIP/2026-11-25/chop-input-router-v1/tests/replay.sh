#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:?workspace}"
repo="${2:?base repository}"
out="${3:?new evidence dir}"
mkdir -p "$out"; out="$(cd "$out" && pwd)"
base=11c14a1c41971067c7dc97db69375f720a408f68
test "$(git -C "$repo" rev-parse "$base:HavenlineLevel1")" = d764a05246cbff96983aa27af17e2e919a946ae0
orig="$here/../chop-impact-retirement-v1"
test -f "$orig/source/chop_impact_bridge.gd"
(cd "$orig"; sha256sum -c SHA256SUMS >/dev/null)
tmp="$(mktemp -d /tmp/hvn-chop-router.XXXXXX)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp"/{p,home,config,data,cache,state,runtime,t}
chmod 700 "$tmp/runtime"
git -C "$repo" archive "$base" HavenlineLevel1 | tar xf - --strip-components=1 -C "$tmp/p"
python "$tmp/p/tools/hydrate_assets.py" > "$out/hydrate.log"
cp "$orig/source/chop_impact_bridge.gd" "$here/source/chop_input_router.gd" "$here/tests/test_router.gd" "$tmp/p/"
cp "$orig/tests/test_chop_impact.gd" "$orig/tests/test_retirement.gd" "$tmp/p/"
cp "$tmp/p/opening.gd" "$tmp/original.gd"
python "$here/tests/overlay.py" "$tmp/p/opening.gd"
diff -u --label original-opening.gd --label test-only-opening.gd "$tmp/original.gd" "$tmp/p/opening.gd" > "$out/test-only.diff" || test "$?" -eq 1
export HOME="$tmp/home" XDG_CONFIG_HOME="$tmp/config" XDG_DATA_HOME="$tmp/data" XDG_CACHE_HOME="$tmp/cache" XDG_STATE_HOME="$tmp/state" XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp/t"
(
 flock -n 8 || exit 75
 flock -n 9 || exit 75
 if ps -eo comm | grep -x godot; then exit 76; fi
 timeout 90s godot --headless --path "$tmp/p" --editor --import > "$out/import.log" 2>&1
 for t0 in test_router test_chop_impact test_retirement; do
  timeout 60s godot --headless --path "$tmp/p" --script "res://$t0.gd" > "$out/$t0.log" 2>&1
 done
) 8<>"$root/.havenline-renderer.lock" 9<>/tmp/havenline-godot-headless.lock
