#!/bin/bash
set -euo pipefail
base=$(realpath "$1"); repo=$(realpath "$2"); w=$(realpath "$3")
d=$(cd "$(dirname "$0")";pwd)
bash "$d/../hvn-l1-wood-paid-carry-capture-v1/stage.sh" "$base" "$repo" "$w"
# Already copied a disposable paid-pine implementation and verified all original pins there.
cd "$w/project"
patch --fuzz=0 -p2 < "$d/display-only.patch"
test "$(git hash-object wood_stock_view.gd)" = f1a892ccb8b346580537107e1a4fff7dcdf156be
test "$(git hash-object previews/integrated_opening.gd)" = b0b09db8b3634b4308d327cefce463f86d2a71db
test "$(sha256sum assets/studio/starter_ground_wood_lod.glb | cut -d' ' -f1)" = 31378ac3c6b21fbc0fdcfe597333794a7fe8b36c628a53956ad6bc0956fd1554
cp "$d/probe.gd" tests/paid_two_visual_probe.gd
