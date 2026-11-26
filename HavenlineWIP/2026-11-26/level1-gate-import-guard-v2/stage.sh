#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
old=$(realpath -e -- "$1")
test "$(sha256sum "$old/SHA256SUMS" | cut -d' ' -f1)" = 9aa2a8bfbdcd1d9881d55825263a53cba182c729d641f691f5f28b4fb4e6305a
(cd "$old"; sha256sum -c --status SHA256SUMS)
(cd "$old/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
test ! -e staged
mkdir staged
cp -a "$old/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
cp clearance_gate_view.gd "$p/previews/clearance_gate/"
cp gate-config.json "$p/previews/clearance_gate/import_census.json"
cp gate-config.json "$p/tests/hvn_l1_gate_config.json"
cp clearance_draw.gd "$p/tests/hvn_l1_combined_draw.gd"
python3 -B verify_stage.py "$old/staged/HavenlineLevel1" "$p" > staged-delta.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
