#!/bin/bash
set -euo pipefail
stage=$(realpath "$1")
crown=$(realpath "$2")
cd "$(dirname "$0")"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
profile=$(mktemp -d "$PWD/cpuprofile.XXXXXX")
trap 'rm -rf "$profile"' EXIT
for k in home config cache data runtime tmp; do mkdir -m 700 "$profile/$k"; done
export HOME="$profile/home" XDG_CONFIG_HOME="$profile/config" XDG_CACHE_HOME="$profile/cache" XDG_DATA_HOME="$profile/data" XDG_RUNTIME_DIR="$profile/runtime" TMPDIR="$profile/tmp"
timeout 90 blender -b -t 2 --python-exit-code 15 -P render.py -- "$stage" "$crown" stocked "$profile/Stage.blend" > render-LOCAL.log 2>&1
grep -E '^Blender|^STAGE|^Time:' render-LOCAL.log > render-sanitized.log
test -s frame-LOCAL.png
