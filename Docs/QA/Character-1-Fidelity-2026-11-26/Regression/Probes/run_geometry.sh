#!/bin/bash
set -euo pipefail
project=$(realpath "$1")
out=$(realpath -m "$2")
probe_dir=$(dirname "$(realpath "$0")")
mkdir -p "$out"
temporary=$(mktemp -d /tmp/havenline-l1-v3-fidelity-XXXXXX)
trap 'rm -rf "$temporary"' EXIT
export XDG_DATA_HOME="$temporary/data" XDG_CONFIG_HOME="$temporary/config" XDG_CACHE_HOME="$temporary/cache"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LP_NUM_THREADS=1
export HAVENLINE_GEAR_GEOMETRY="$temporary/geometry" HAVENLINE_PROBE_RESULTS="$out"
mkdir "$HAVENLINE_GEAR_GEOMETRY"
echo HAVENLINE-ALFRED-V3-DISPOSABLE > "$temporary/L1-DISPOSABLE"
godot --headless --audio-driver Dummy --fixed-fps 60 --frame-delay 5 --audio-output-latency 5 --path "$project" --script "$probe_dir/capture_geometry.gd" -- "--l1-disposable-profile=$temporary" > "$out/imported-geometry.log" 2>&1
godot --headless --audio-driver Dummy --fixed-fps 60 --audio-output-latency 5 --frame-delay 5 --path "$project" --script "$probe_dir/capture_body.gd" -- "--l1-disposable-profile=$temporary" > "$out/body-capture.log" 2>&1
blender -b -t 1 --python-exit-code 1 --python "$probe_dir/clear_body.py" > "$out/body-audit.log" 2>&1
blender -b -t 1 --python-exit-code 1 --python "$probe_dir/triangle_audit.py" > "$out/triangles.log" 2>&1
python "$probe_dir/radial_clearance.py"
python "$probe_dir/support.py" > "$out/support.log"
