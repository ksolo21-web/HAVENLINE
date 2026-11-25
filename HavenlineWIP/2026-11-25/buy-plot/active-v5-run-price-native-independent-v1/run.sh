#!/bin/bash
set -euo pipefail
dir=$(cd "$(dirname "$0")";pwd)
base=$(realpath "$1"); repo=$(realpath "$2"); w=$(realpath "$3")
test -d "$w" && test -z "$(ls -A "$w")"
cd "$dir"
repair="$dir/../hvn-l1-v5-run-price-repair-v1"
pine="$dir/../hvn-l1-paid-pine-renewal-v1"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock; flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test "$(sha256sum "$repair/SHA256SUMS"|cut -d' ' -f1)" = 0e224a741fb87cd6459924517fce95d523c0aabb1fa22ce02c76cf56197bab96
(cd "$repair"; sha256sum -c SHA256SUMS)
test "$(sha256sum "$pine/renewal.patch"|cut -d' ' -f1)" = e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd
cp -a "$base" "$w/project"
cd "$w/project"
pin=11c14a1c41971067c7dc97db69375f720a408f68
files=(opening.gd opening_ledger.gd opening_save.gd resource_tree.gd pad_v5_view.gd purchase_pad_visual.gd previews/integrated_opening.gd previews/integrated_opening.tscn previews/hero_locomotion.gd assets/characters/Character1.glb tests/test_integrated_opening.gd project.godot)
for f in "${files[@]}"; do test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1/$f")"; done
test "$(sha256sum assets/studio/purchase_pad_v5.glb|cut -d' ' -f1)" = d938ed53778f135359d4a345603a84353a7d02daddc0ff6e389453101119b7cb
test "$(sha256sum assets/studio/hearth_trial_02.glb|cut -d' ' -f1)" = 35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a
patch --fuzz=0 -p2 < "$repair/updated-location-only.patch"
patch --fuzz=0 -p2 < "$pine/renewal.patch"
test "$(git hash-object pad_v5_view.gd)" = a39b99e1c7c060eed80b469132d21a251b0b6f83
test "$(git hash-object opening_ledger.gd)" = 2e713651f3a75a45db6e6577e48f7361ad37e127
test "$(git hash-object previews/integrated_opening.gd)" = ca88b482831e0898b488be6efa63caf691f2eb95
for f in "${files[@]}"; do
 case "$f" in opening_ledger.gd|pad_v5_view.gd|previews/integrated_opening.gd) ;; *) test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1/$f")";; esac
done
cp "$dir/route.gd" tests/indep_v5_run_price.gd
profile=$(mktemp -d /tmp/havenline-l1-v3-v5reprice-XXXXXX)
trap 'rm -rf "$profile"' EXIT
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
for k in funded cold; do
 m="$w/$k"; mkdir -p "$m"/{home,config,cache,data,runtime,tmp}; chmod 700 "$m/runtime"
 HOME="$m/home" XDG_CONFIG_HOME="$m/config" XDG_CACHE_HOME="$m/cache" XDG_DATA_HOME="$m/data" XDG_RUNTIME_DIR="$m/runtime" TMPDIR="$m/tmp" HVN_OUT="$m" HVN_ROUTE="$k" timeout 75s godot --headless --fixed-fps 60 --path "$w/project" --script res://tests/indep_v5_run_price.gd -- "--l1-disposable-profile=$profile" > "$m/log" 2>&1
 ! grep -E 'ERROR|WARNING|FAIL' "$m/log"
 grep -E '^(Godot|PASS|COMBINED_COUNT)' "$m/log" > "$dir/$k-sanitized.log"
done
