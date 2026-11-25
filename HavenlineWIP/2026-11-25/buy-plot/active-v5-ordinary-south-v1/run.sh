#!/bin/bash
set -euo pipefail
source_dir=$(realpath "$1")
gitdir=$(realpath "$2")
dir=$(cd "$(dirname "$0")";pwd)
out=$(realpath "$3")
test -z "$(pgrep -x godot || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)"
cp -a "$source_dir" "$out/project"
cd "$out/project"
rev=11c14a1c41971067c7dc97db69375f720a408f68
for f in opening.gd pad_v5_view.gd purchase_pad_visual.gd previews/integrated_opening.gd previews/integrated_opening.tscn previews/hero_locomotion.gd assets/characters/Character1.glb tests/test_integrated_opening.gd; do
  test "$(git hash-object "$f")" = "$(git -C "$gitdir" rev-parse "$rev:HavenlineLevel1/$f")"
done
test "$(sha256sum assets/studio/purchase_pad_v5.glb |cut -d' ' -f1)" = d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb
cp "$dir/route.gd" tests/ordinary_v5_south_capture.gd
for k in unfunded funded; do
  mode="$out/$k"
  mkdir -p "$mode"/{home,config,cache,data,runtime,tmp}
  chmod 700 "$mode/runtime"
  HOME="$mode/home" XDG_CONFIG_HOME="$mode/config" XDG_CACHE_HOME="$mode/cache" XDG_DATA_HOME="$mode/data" XDG_RUNTIME_DIR="$mode/runtime" TMPDIR="$mode/tmp" HVN_OUT="$mode" HVN_ROUTE="$k" timeout 50s godot --headless --fixed-fps 60 --path . --script res://tests/ordinary_v5_south_capture.gd > "$mode/log" 2>&1
  ! grep -E 'ERROR|WARNING' "$mode/log"
done
