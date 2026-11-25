#!/bin/bash
set -euo pipefail
repo="$(realpath "$1")"
base="$(realpath "$2")"
author="$(realpath "$3")"
qa="$(cd "$(dirname "$0")"; pwd)"
cd "$qa"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock; flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test "$(sha256sum "$author/SHA256SUMS" | cut -d' ' -f1)" = 2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f
(cd "$author"; sha256sum -c SHA256SUMS)
test "$(sha256sum "$author/renewal.patch"|cut -d' ' -f1)" = e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd
w=$(mktemp -d "$qa/../hvn-pine-replay-LOCAL.XXXXXX")
profile="$(mktemp -d /tmp/havenline-l1-v3-pinei-XXXXXX)"
trap 'rm -rf "$w" "$profile"' EXIT
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
cp -a "$base" "$w/project"
cd "$w/project"
sha=11c14a1c41971067c7dc97db69375f720a408f68
pinned=(opening_ledger.gd previews/integrated_opening.gd opening.gd resource_tree.gd opening_save.gd project.godot previews/integrated_opening.tscn tests/test_integrated_opening.gd)
for f in "${pinned[@]}"; do test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$sha:HavenlineLevel1/$f")"; done
test "$(sha256sum assets/studio/hearth_trial_02.glb|cut -d' ' -f1)" = 35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a
patch --fuzz=0 -p2 < "$author/renewal.patch"
for f in opening.gd resource_tree.gd opening_save.gd project.godot previews/integrated_opening.tscn tests/test_integrated_opening.gd; do test "$(git hash-object "$f")" = "$(git -C "$repo" rev-parse "$sha:HavenlineLevel1/$f")"; done
cp "$qa/observer.gd" tests/indep_paid_pine_observer.gd
cp "$qa/replay.gd" tests/indep_paid_pine_replay.gd
for k in home cache config data runtime tmp; do mkdir -m 700 "$w/$k"; done
export HOME="$w/home" XDG_CONFIG_HOME="$w/config" XDG_CACHE_HOME="$w/cache" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp"
timeout 75s godot --headless --fixed-fps 60 --path "$w/project" --script res://tests/indep_paid_pine_replay.gd -- "--l1-disposable-profile=$profile" > "$qa/raw.log" 2>&1
! grep -E 'ERROR|WARNING|FAIL' "$qa/raw.log"
grep -E '^(Godot|PASS|INDEPENDENT_COUNT)' "$qa/raw.log" > "$qa/replay-sanitized.log"
