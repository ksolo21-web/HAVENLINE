#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
base=$(realpath -e -- "$1")
draft=$(realpath -e -- "$2")
test "$(sha256sum "$base/SHA256SUMS" | cut -d' ' -f1)" = 520fbaf940f51c8f2b63299d406092ae83bc4b339f60f49852923be9a73022c5
test "$(sha256sum "$draft/SHA256SUMS" | cut -d' ' -f1)" = 1fd412a4c194af327d3b3a4949dd5fe03928a1fef593d9cebae761555a24a759
(cd "$base"; sha256sum -c --status SHA256SUMS)
(cd "$draft"; sha256sum -c --status SHA256SUMS)
(cd "$base/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
q="$p/previews/reference_panel"
mkdir -p "$q/assets"
cp reference_panel.{gd,tscn} "$q/"
cp "$draft/candidate/fence_reference_detail.obj" "$draft/candidate/reference_detail.mtl" "$q/assets/"
python3 -B "$draft/verify.py" "$q/assets/fence_reference_detail.obj" "$p/previews/r17_fence/assets/fence_panel.obj" > authored-mesh.json
python3 - "$p/tests/hvn_l1_combined_route.gd" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_bytes()
before=b'game=preload("res://previews/r17_fence/r17_fence_view.tscn").instantiate()'
after=b'game=preload("res://previews/reference_panel/reference_panel.tscn").instantiate()'
assert s.count(before)==1 and s.count(after)==0
p.write_bytes(s.replace(before,after))
PY
python3 -B adapt_observer.py "$p/tests/hvn_l1_combined_draw.gd"
python3 -B source_receipt.py "$base/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
