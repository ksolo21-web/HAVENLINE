#!/bin/bash
set -euo pipefail
if [ "$#" != 3 ]; then echo 'Usage: stage.sh EXACT_HYDRATED_BASELINE EXACT_GIT_CHECKOUT EMPTY_WORK_DIR' >&2; exit 2; fi
base=$(realpath "$1"); repo=$(realpath "$2"); w=$(realpath "$3")
here=$(cd "$(dirname "$0")";pwd)
pine="$here/../hvn-l1-paid-pine-renewal-v1"
test "$(sha256sum "$pine/renewal.patch"|cut -d' ' -f1)" = e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd
cp -a "$base" "$w/project"
cd "$w/project"
pin=11c14a1c41971067c7dc97db69375f720a408f68
files=(opening.gd opening_ledger.gd opening_save.gd resource_tree.gd technical_gate.gd wood_stock_view.gd terrain_source.gd previews/integrated_opening.gd previews/integrated_opening.tscn previews/hero_locomotion.gd assets/characters/Character1.glb assets/studio/wood_bundle_v3.glb tests/test_integrated_opening.gd project.godot)
for f in "${files[@]}"; do test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1/$f")"; done
test "$(sha256sum assets/studio/hearth_trial_02.glb|cut -d' ' -f1)" = 35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a
patch --fuzz=0 -p2 < "$pine/renewal.patch"
test "$(git hash-object opening_ledger.gd)" = 2e713651f3a75a45db6e6577e48f7361ad37e127
test "$(git hash-object previews/integrated_opening.gd)" = ca88b482831e0898b488be6efa63caf691f2eb95
for f in "${files[@]}"; do case "$f" in opening_ledger.gd|previews/integrated_opening.gd) ;; *) test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1/$f")";; esac; done
cp "$here/capture.gd" tests/paid_carry_capture.gd
for k in home config cache data runtime tmp; do mkdir -m 700 "$w/$k"; done
echo "STAGED_SOURCE_ONLY"
