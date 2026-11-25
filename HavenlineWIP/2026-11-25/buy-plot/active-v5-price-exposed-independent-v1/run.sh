#!/bin/bash
set -euo pipefail
source_dir=$(realpath "$1")
gitdir=$(realpath "$2")
author=$(realpath "$3")
driver=$(realpath "$4")
qa=$(cd "$(dirname "$0")";pwd)
w=$(realpath "$5")
test -d "$w" && test -z "$(ls -A "$w")"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
for manifest in "$author" "$driver"; do (cd "$manifest"; sha256sum -c SHA256SUMS); done
test "$(sha256sum "$author/SHA256SUMS"|cut -d' ' -f1)" = 93475711ec9ede90409a5c2d52fb5912bcfcc2ce0bcd8ffae960ef82eab6afd6
test "$(sha256sum "$driver/SHA256SUMS"|cut -d' ' -f1)" = 7480ea02eba2e75c4a7a073e703470304d4e41f46bb9996285d7d4893146a38a
cp -a "$source_dir" "$w/project"
cd "$w/project"
rev=11c14a1c41971067c7dc97db69375f720a408f68
for p in opening.gd pad_v5_view.gd purchase_pad_visual.gd previews/integrated_opening.gd previews/integrated_opening.tscn previews/hero_locomotion.gd assets/characters/Character1.glb tests/test_integrated_opening.gd; do
 test "$(git hash-object "$p")" = "$(git -C "$gitdir" rev-parse "$rev:HavenlineLevel1/$p")"
done
test "$(sha256sum assets/studio/purchase_pad_v5.glb|cut -d' ' -f1)" = d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb
cp "$driver/route.gd" tests/ordinary_v5_south_capture.gd
for a in base candidate; do
 if [ "$a" = candidate ]; then
  patch --fuzz=0 -p2 < "$author/cost-location-only.patch"
  test "$(git hash-object pad_v5_view.gd)" = 10c747bf0b47afaf76a4eb992cba25f7d445ff24
 fi
 for b in unfunded funded; do
  p="$w/$a/$b"
  mkdir -p "$p"/{home,config,cache,data,runtime,tmp}
  chmod 700 "$p/runtime"
  HOME="$p/home" XDG_CONFIG_HOME="$p/config" XDG_CACHE_HOME="$p/cache" XDG_DATA_HOME="$p/data" XDG_RUNTIME_DIR="$p/runtime" TMPDIR="$p/tmp" HVN_OUT="$p" HVN_ROUTE="$b" timeout 45s godot --headless --fixed-fps 60 --path . --script res://tests/ordinary_v5_south_capture.gd > "$p/log" 2>&1
  ! grep -E 'ERROR|WARNING|FAIL' "$p/log"
  grep '^PASS ' "$p/log" >> "$qa/native-pass-sanitized.log"
 done
done
patch --reverse --fuzz=0 -p2 < "$author/cost-location-only.patch"
test "$(git hash-object pad_v5_view.gd)" = 43f88e9deebb74d5eaf69290ced38681f59a8b36
