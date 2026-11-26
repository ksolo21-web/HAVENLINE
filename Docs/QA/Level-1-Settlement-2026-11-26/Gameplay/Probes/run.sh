set -eu
p=$(cd -- "$(dirname -- "$0")" && pwd)
g=${HL_GAME_PROJECT:-/workspace/scratch/level1-finish/Game}
r="$1"; plan="$2"; mode="$3"; fps="${4:-24}"
mkdir -p "$r"
export FIELD_QA_OUTPUT="$r" FIELD_QA_PLAN="$plan" FIELD_QA_SCENE=res://field_opening.tscn XDG_DATA_HOME="$r/xdg" XDG_CONFIG_HOME="$r/config" XDG_CACHE_HOME=/dev/shm/havenline-gait/capture/cache OPENBLAS_NUM_THREADS=1 LP_NUM_THREADS=2
if test -n "${RESUME_PROFILE:-}"; then profile="$RESUME_PROFILE"; else
 profile=$(mktemp -d /tmp/havenline-l1-v3-finish-XXXXXXXX)
 echo HAVENLINE-ALFRED-V3-DISPOSABLE > "$profile/L1-DISPOSABLE"
fi
echo "$profile" > "$r/profile"
if test "$mode" = headless; then
 export FIELD_QA_HEADLESS=1
 args=(--headless --audio-driver Dummy)
else
 export HL_RECORD=1 HL_OUTPUT_FPS="$fps" DISPLAY=${HL_DISPLAY:-:111} XAUTHORITY=${HL_XAUTHORITY:-/tmp/hvn95-release/review-auth} LIBGL_ALWAYS_SOFTWARE=1
 python "$p/encoder.py" "$r" "$fps" >"$r/encoder.log" 2>&1 &
 encoder=$!
 until test -s "$r/socket-port"; do sleep .05; done
 export HL_STREAM_PORT=$(cat "$r/socket-port")
 touch "$r/discard.avi"
 python "$p/spool.py" "$r/discard.avi" > "$r/spool.log" 2>&1 &
 spool_pid=$!
 args=(--write-movie "$r/discard.avi" --windowed --resolution 1280x720 --disable-render-loop)
fi
status=0
godot --path "$g" --fixed-fps "$fps" "${args[@]}" --script "$p/stream.gd" -- "--l1-disposable-profile=$profile" > "$r/game.log" 2>&1 || status=$?
if test -n "${encoder:-}"; then
 touch "$r/encoder-finished"
 wait "$encoder" || status=1
 wait "$spool_pid" || status=1
 unlink "$r/discard.avi"
fi
exit "$status"
