#!/bin/bash
set -euo pipefail
# Owner workflow's sole actual renderer grant must be confirmed independently.
[[ "${HAVENLINE_SOLE_RENDER_GRANT:-}" == one-far-receiver-still ]]
test "$#" = 9
p=$(cd "$(dirname "$0")" && pwd)
args=()
for i in {1..8}; do args+=("$(realpath "$1")");shift;done
dest=$(realpath -m "$1");test ! -e "$dest";test -d "$(dirname "$dest")"
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -x godot || true)$(pgrep -x blender || true)"
d=$(mktemp -d "$p/render-owned.XXXXXX");trap 'rm -rf -- "$d"' EXIT
for n in home cache conf data run tmp out;do mkdir -m 700 "$d/$n";done
export HOME="$d/home" TMPDIR="$d/tmp" XDG_CACHE_HOME="$d/cache" XDG_CONFIG_HOME="$d/conf" XDG_DATA_HOME="$d/data" XDG_RUNTIME_DIR="$d/run"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1
ulimit -f 16384 # any regular output file <=16 MiB; each media file has its own 4 MB cap
timeout 70 blender -b -t 2 --python-exit-code 15 -P "$p/render_once.py" -- "${args[@]}" "$d/out" >"$d/private.log" 2>&1 || { tail -30 "$d/private.log" >&2;exit 1; }
python - "$d/out" <<'PY'
from pathlib import Path
from PIL import Image
import sys
d=Path(sys.argv[1]);assert sorted(x.name for x in d.iterdir())==['two-settled-far.png']
for p in d.iterdir():
 with Image.open(p) as img:assert img.size==(1280,720);img.load()
 assert p.stat().st_size<=4_000_000
PY
mv -- "$d/out" "$dest"
