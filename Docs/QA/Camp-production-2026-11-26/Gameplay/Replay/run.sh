#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
game=${HL_GAME_PROJECT:-/workspace/scratch/camp-processing/Game}
output=$1
plan=$2
mode=${3:-headless}
fps=${4:-16}
mkdir -p "$output"
profile=$(mktemp -d /tmp/havenline-l1-v3-camp-film-XXXXXXXX)
echo HAVENLINE-ALFRED-V3-DISPOSABLE > "$profile/L1-DISPOSABLE"
cp "$here/earned-input.save.json" "$profile/field-inventory-v1.json"
echo "$profile" > "$output/disposable-profile"
export XDG_DATA_HOME="$output/xdg-data" XDG_CONFIG_HOME="$output/xdg-config" XDG_CACHE_HOME="$output/xdg-cache"
export FIELD_QA_PLAN="$plan" FIELD_QA_OUTPUT="$output" FIELD_QA_SCENE=res://field_opening.tscn LP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1
export HL_OUTPUT_FPS=$fps
if [[ "$mode" == headless ]]; then
    export FIELD_QA_HEADLESS=1
    args=(--headless --audio-driver Dummy)
elif [[ "$mode" == plates ]]; then
    export HL_PLATES=1 DISPLAY=${HL_DISPLAY:-:111} XAUTHORITY=${HL_XAUTHORITY:-/tmp/hvn95-release/review-auth} LIBGL_ALWAYS_SOFTWARE=1
    args=(--fullscreen --resolution 3840x2160 --disable-render-loop --audio-driver Dummy)
else
    export HL_RECORD=1 DISPLAY=${HL_DISPLAY:-:111} XAUTHORITY=${HL_XAUTHORITY:-/tmp/hvn95-release/review-auth} LIBGL_ALWAYS_SOFTWARE=1
    python "$here/encoder.py" "$output" "$fps" > "$output/encoder.log" 2>&1 &
    enc=$!
    until test -s "$output/socket-port"; do sleep .05; done
    export HL_STREAM_PORT=$(cat "$output/socket-port")
    touch "$output/movie-scratch.avi"
    python "$here/spool.py" "$output/movie-scratch.avi" > "$output/spool.log" 2>&1 &
    spool=$!
    args=(--write-movie "$output/movie-scratch.avi" --windowed --resolution 1280x720 --disable-render-loop)
fi
rc=0
godot --path "$game" --fixed-fps "$fps" "${args[@]}" --script "$here/film.gd" -- "--l1-disposable-profile=$profile" > "$output/godot.log" 2>&1 || rc=$?
if [[ -n "${enc:-}" ]]; then
    touch "$output/encoder-finished"
    wait "$enc" || rc=1
    wait "$spool" || rc=1
    unlink "$output/movie-scratch.avi"
fi
exit "$rc"
