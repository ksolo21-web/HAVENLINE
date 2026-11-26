#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
old=$(realpath -e -- "$1")
auth=$(realpath -e -- "$2")
test "$(sha256sum "$old/SHA256SUMS" | cut -d' ' -f1)" = d352e28408a87328d6a1ceec1fabe6f3c21eac5c37c2a9c0623ca9f04208d829
test "$(sha256sum "$auth/SHA256SUMS" | cut -d' ' -f1)" = 349fcbb88c66469cfc50f8c4d2e84249a68a2954378836e78ab9b3f2e19e006c
(cd "$old"; sha256sum -c --status SHA256SUMS)
(cd "$auth"; sha256sum -c --status SHA256SUMS)
(cd "$old/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
for f in material_reference_paint.gdshader material-map.json; do cmp "$f" "$auth/$f"; done
test ! -e staged
mkdir staged
cp -a "$old/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
q="$p/previews/reference_panel/assets"
cp material_reference_paint.gdshader material-map.json "$q/"
python3 -B adapt.py "$p"
python3 -B check_stage.py "$old/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
