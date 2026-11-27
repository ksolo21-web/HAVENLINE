#!/usr/bin/env bash
set -euo pipefail
task=/tmp/havenline-t01-closure
out="$task/$1"
profile=$2
export T01_SIZE="${3:-460x760}" T01_OUT="$out"
export XDG_DATA_HOME="$out/data" XDG_CONFIG_HOME="$out/config" XDG_CACHE_HOME="$task/cache"
export LP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 DISPLAY=:111 XAUTHORITY=/tmp/hvn95-release/review-auth LIBGL_ALWAYS_SOFTWARE=1 MESA_SHADER_CACHE_DISABLE=true
userdata="$XDG_DATA_HOME/Havenline-Level-1-Settlement-Trial"
mkdir -p "$userdata/world-one" "$task/shader-cache"
ln -s "$task/shader-cache" "$userdata/shader_cache"
if [ "$profile" = paid ]; then
  cp /workspace/shared/downloads/Havenline/camp13/Source/Fixtures/Build8-cooker-only.json "$userdata/world-one/field-inventory-v1.json"
fi
cd "${T01_SCENE_ROOT:-/dev/shm/hl15game}"
sha256sum field_environment.gd field_thumbstick.gd field_forest.gd field_resource_sightline.gd field_opening.gd world_landscape.gd assets/field_world/{resource_sightline.gdshader,character_sightline.gdshaderinc} assets/reference_forest/pine_*.glb assets/reference_forest/bank_pine_*.glb* > "$out/source.sha256"
flock /tmp/hl13/render.lock timeout 140 godot --disable-render-loop --rendering-method gl_compatibility --windowed --resolution "$T01_SIZE" --audio-driver Dummy --fixed-fps 60 --script "$task/capture.gd" > "$out/native.log" 2>&1
