#!/usr/bin/env bash
set -euo pipefail
base=$(realpath -e -- "$1")
cd -- "$(dirname -- "$0")"
test "$(sha256sum "$base/SHA256SUMS" | cut -d' ' -f1)" = d6662929e793265b0bb0b7b147be2ce23cd5e5ef54643bc68ee5951b33e3d580
(cd "$base"; sha256sum -c --status SHA256SUMS; cd staged/HavenlineLevel1; sha256sum -c --status ../draw-source.sha256)
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
cp active_close.gd "$p/tests/hvn_l1_active_close.gd"
python3 -B verify_stage.py "$base/staged/HavenlineLevel1" "$p" > staged-delta.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
