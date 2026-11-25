#!/bin/bash
set -euo pipefail
d=$(cd "$(dirname "$0")" && pwd); a=$(realpath "$1"); b=$(realpath "$2"); c=$(realpath "$3")
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
test "$(df -m "$d" | awk 'END {print $4}')" -gt 230
w=$(mktemp -d "$d/owned.XXXXXX")
trap 'rm -rf -- "$w"' EXIT
for v in home cache conf data runtime tmp; do mkdir -m 700 "$w/$v"; done
export HOME="$w/home" XDG_CACHE_HOME="$w/cache" XDG_CONFIG_HOME="$w/conf" XDG_DATA_HOME="$w/data" XDG_RUNTIME_DIR="$w/runtime" TMPDIR="$w/tmp" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
if ! timeout 230 blender -b -t 2 --python-exit-code 15 -P "$d/render.py" -- "$a" "$b" "$c" "$w" "$w/stock-walk-run.mp4" >"$w/render.log" 2>&1; then
 tail -35 "$w/render.log" | sed "s@$w@<own-work>@g" >"$d/first-failure.log"; exit 3
fi
ffprobe -v error -count_frames -show_entries stream=width,height,avg_frame_rate,nb_read_frames,duration,codec_name -of json "$w/stock-walk-run.mp4" >"$d/media-meta.json"
python - "$d/media-meta.json" <<'PY'
from pathlib import Path
import json,sys
s,=json.loads(Path(sys.argv[1]).read_bytes())['streams']
assert (s['width'],s['height'],s['avg_frame_rate'],int(s['nb_read_frames']))==(1280,720,'15/1',45)
PY
test "$(df -m "$d" | awk 'END {print $4}')" -ge 200
mv "$w/stock-walk-run.mp4" "$d/stock-walk-run.LOCAL.mp4"
