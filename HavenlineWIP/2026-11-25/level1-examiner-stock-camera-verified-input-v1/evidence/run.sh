#!/bin/bash
# Execute only if root explicitly grants this one renderer slot.
set -euo pipefail
d=$(cd "$(dirname "$0")" && pwd)
test "$#" = 5
m=$(realpath "$1"); stage=$(realpath "$2"); crown=$(realpath "$3"); actor=$(realpath "$4")
dest=$(realpath -m "$5")
test ! -e "$dest"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
p=$(mktemp -d "$d/render-owned.XXXXXX")
trap 'rm -rf -- "$p"' EXIT
for name in home cache conf data run tmp; do mkdir -m 700 "$p/$name"; done
export HOME="$p/home" XDG_CACHE_HOME="$p/cache" XDG_CONFIG_HOME="$p/conf" XDG_DATA_HOME="$p/data" XDG_RUNTIME_DIR="$p/run" TMPDIR="$p/tmp"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
timeout 420 blender -b -t 2 --python-exit-code 15 -P "$d/render_stage_motion.py" -- "$m" "$stage" "$crown" "$actor" "$p" "$p/stock-camera-review.mp4" > "$p/private.log" 2>&1
ffprobe -v error -count_frames -show_entries stream=width,height,avg_frame_rate,nb_read_frames -of json "$p/stock-camera-review.mp4" >"$p/meta.json"
python - "$m" "$p/meta.json" <<'PY'
from pathlib import Path
import json,sys
s,=json.loads(Path(sys.argv[2]).read_bytes())['streams']
m=json.loads(Path(sys.argv[1]).read_bytes())
assert (s['width'],s['height'],s['avg_frame_rate'],int(s['nb_read_frames']))==(1280,720,'15/1',len(m['frames'])+8)
PY
mv -- "$p/stock-camera-review.mp4" "$dest"
