#!/bin/bash
set -euo pipefail
dir=$(cd "$(dirname "$0")"; pwd)
source_dir=$(realpath "$1")
candidate=$(realpath "$2")
cd "$dir"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
w=$(mktemp -d /tmp/hvn-v5-price-independent.XXXXXX)
trap 'rm -rf "$w"' EXIT
for name in home config cache data runtime tmp; do mkdir "$w/$name"; done
chmod 700 "$w/runtime"
export HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp"
p="$w/HavenlineLevel1"
cp -a "$source_dir" "$p"
cd "$p"
test "$(git hash-object pad_v5_view.gd)" = 43f88e9deebb74d5eaf69290ced38681f59a8b36
test "$(git hash-object purchase_pad_visual.gd)" = 4b00374a0871b451bf306bd26b3d329fb34a7aaf
test "$(sha256sum assets/studio/purchase_pad_v5.glb | cut -d' ' -f1)" = d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb
cp "$dir/native_probe.gd" tests/v5_price_independent.gd
for variant in base trial; do
 if [ "$variant" = trial ]; then
  patch -p1 < "$candidate/typography-only.patch"
  test "$(git hash-object pad_v5_view.gd)" = "$(tail -1 "$candidate/patch-blob-provenance.txt" | awk '{print $NF}')"
 fi
 timeout 30s godot --headless --fixed-fps 60 --path "$p" --script res://tests/v5_price_independent.gd > "$dir/$variant-run.log" 2>&1
 test "$(grep -c '^V5_PRICE ' "$dir/$variant-run.log")" = 1
 ! grep -E 'ERROR|WARNING' "$dir/$variant-run.log"
 sed -n 's/^V5_PRICE //p' "$dir/$variant-run.log" > "$dir/$variant-native.json"
done
