#!/usr/bin/env bash
set -euo pipefail
label=$1
route=$2
mode=$3
game=${T01_GAME:-/dev/shm/hl15game}
test=${T01_TEST:-/tmp/havenline-beta-t01/independent/route.gd}
out=/tmp/havenline-beta-t01/independent/$label
mkdir -p "$out"
export T01_OUT="$out" T01_ROUTE="$route" XDG_DATA_HOME="$out/data" XDG_CONFIG_HOME="$out/config" XDG_CACHE_HOME="$out/cache" LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
folder="$XDG_DATA_HOME/Havenline-Level-1-Settlement-Trial/world-one"
mkdir -p "$folder"
fixture=${T01_FIXTURE:-/workspace/shared/downloads/Havenline/camp13/Source/Fixtures/Build8-cooker-only.json}
cp "$fixture" "$folder/field-inventory-v1.json"
sha256sum "$fixture" > "$out/fixture.sha256"
cd "$game"
sha256sum field_forest.gd world_landscape.gd field_survivor.gd field_resource_sightline.gd field_opening.gd assets/field_world/resource_sightline.gdshader conifers.json assets/reference_forest/pine_*.glb > "$out/source.sha256"
if [ "$mode" = native ]; then
  export T01_IMAGES=1 DISPLAY=:111 XAUTHORITY=/tmp/hvn95-release/review-auth LIBGL_ALWAYS_SOFTWARE=1
  flock /tmp/hl13/render.lock timeout 200 godot --disable-render-loop --rendering-method gl_compatibility --windowed --resolution 460x760 --audio-driver Dummy --fixed-fps 60 --script "$test" > "$out/native.log" 2>&1
else
  timeout 140 godot --headless --audio-driver Dummy --fixed-fps 60 --script "$test" > "$out/native.log" 2>&1
fi
