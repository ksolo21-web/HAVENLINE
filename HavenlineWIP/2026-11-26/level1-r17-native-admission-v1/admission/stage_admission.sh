#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
f=$(realpath -e -- "$1")
test "$(sha256sum "$f/SHA256SUMS" | cut -d' ' -f1)" = 24f67ef16db41b198bca62f2058297bb9f0e36f5cb7798e733da92ad8a74f43b
(cd "$f"; sha256sum -c --status SHA256SUMS)
test ! -e staged
mkdir -p staged
cp -a "$f/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
(cd "$p"; sha256sum -c --status "$f/staged/final.sha256")
cp "$f/staged/final.sha256" staged/final.sha256
python3 "$f/verify_static.py" "$p" >/dev/null
test "$(sha256sum stock-route.gd | cut -d' ' -f1)" = 1f42c7a29a34c24a3bb22f51743eb878ac2fc18d8c729394cf3ae11915ebbfd1
cmp stock-route.gd "$p/tests/hvn_l1_combined_route.gd"
python3 - "$p/tests/hvn_l1_combined_route.gd" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1])
before=s.read_bytes()
old=b'game=GAME.instantiate()'
new=b'game=preload("res://previews/r17_fence/r17_fence_view.tscn").instantiate()'
assert before.count(old)==1
v=before.replace(old,new)
assert v.count(new)==1 and v.replace(new,old)==before
s.write_bytes(v)
PY
cp draw_route.gd "$p/tests/hvn_l1_combined_draw.gd"
test "$(find "$p" -type f | wc -l)" -eq 137
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
