#!/usr/bin/env bash
set -euo pipefail
stage=/tmp/havenline-t01-closure
out="$stage/$1-regression"
mkdir -p "$out"
cd "${T01_SCENE_ROOT:-/dev/shm/hl15game}"
sha256sum field_environment.gd field_thumbstick.gd field_forest.gd field_resource_sightline.gd field_opening.gd assets/field_world/{resource_sightline.gdshader,character_sightline.gdshaderinc} assets/reference_forest/bank_pine_*.glb* > "$out/source.sha256"
for spec in tests/qa_forest_perimeter_safety.gd qa_field_forest.gd tests/qa_worker_harvest.gd tests/world_landscape_qa.gd tests/qa_field_touch_resume.gd qa_orbit_camera.gd qa_field_environment.gd qa_tree_return.gd tests/qa_fence_orbit.gd "$stage/bank-promotion.gd"; do
  name="${spec##*/}"
  script="$spec"
  if [[ "$spec" != /* ]]; then script="res://$spec"; fi
  export XDG_DATA_HOME="$out/$name/data" XDG_CONFIG_HOME="$out/$name/config" XDG_CACHE_HOME="$stage/cache" LP_NUM_THREADS=1
  timeout 65 godot --headless --audio-driver Dummy --fixed-fps 60 --script "$script" > "$out/$name.log" 2>&1
  printf '%s PASS\n' "$spec"
done
