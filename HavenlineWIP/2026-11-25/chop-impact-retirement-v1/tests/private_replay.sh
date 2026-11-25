#!/usr/bin/env bash
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
root="${1:?workspace root}"
base="${2:?path to pinned repository}"
mode="${3:?baseline or repair}"
out="${4:?log directory}"
if [ "$mode" = baseline ]; then
    original="$here/../chop-impact-bridge-v1"
    test "$(sha256sum "$original/SHA256SUMS" | awk '{print $1}')" = a3d952ab30a934464240832c101c9dcb803ca958f968f16dd15a33b3419d4cc6
    (cd "$original" && sha256sum -c SHA256SUMS >/dev/null)
    bridge="$original/source/chop_impact_bridge.gd"
else
    test "$mode" = repair
    bridge="$here/source/chop_impact_bridge.gd"
fi
tmp="$(mktemp -d /tmp/hvn-chop-retirement.XXXXXX)"
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp"/{p,home,config,data,cache,state,runtime,t}
chmod 700 "$tmp/runtime"
for f in resource_tree.gd opening_ledger.gd; do git -C "$base" show 11c14a1c41971067c7dc97db69375f720a408f68:HavenlineLevel1/"$f" > "$tmp/p/$f"; done
cp "$bridge" "$tmp/p/chop_impact_bridge.gd"
cp "$here/tests/"*.gd "$tmp/p/"
printf 'config_version=5\n\n[application]\nconfig/name="DetachedChopRetirement"\n\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n' > "$tmp/p/project.godot"
export HOME="$tmp/home" XDG_CONFIG_HOME="$tmp/config" XDG_DATA_HOME="$tmp/data" XDG_CACHE_HOME="$tmp/cache" XDG_STATE_HOME="$tmp/state" XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp/t"
mkdir -p "$out"
(
 flock -n 8 || exit 75
 flock -n 9 || exit 75
 if ps -eo comm | grep -x godot; then exit 76; fi
 timeout 25s godot --headless --path "$tmp/p" --editor --import > "$out/$mode-import.log" 2>&1
 set +e
 timeout 25s godot --headless --path "$tmp/p" --script res://test_retirement.gd > "$out/$mode-retirement.log" 2>&1
 ret=$?
 set -e
 if [ "$mode" = baseline ]; then
   test "$ret" -eq 1
 else
   test "$ret" -eq 0
   timeout 25s godot --headless --path "$tmp/p" --script res://test_chop_impact.gd > "$out/$mode-original.log" 2>&1
 fi
) 8<>"$root/.havenline-renderer.lock" 9<>/tmp/havenline-godot-headless.lock
