#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname "$0")"
old=$(realpath -e ../hvn-l1-funded-stock-pad-native-ephemeral-v1)
test "$(sha256sum "$old/SHA256SUMS" | cut -d' ' -f1)" = 7a1b0bda136f1433d1ad481b0f375f6c3af95d676b8d54d3f3d7b3f0c0549a92
(cd "$old"; sha256sum -c --status SHA256SUMS; cd staged/project; sha256sum -c --status ../final.sha256)
test ! -e staged
mkdir staged
cp -a "$old/staged/project" staged/
p=staged/project
test ! -e "$p/tests/c1_normal_stock_capture.gd"
cp observer.gd "$p/tests/c1_normal_stock_capture.gd"
(cd "$p"; sha256sum -c --status "$old/staged/final.sha256"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/final.sha256
python3 -B verify_stage.py "$old/staged/final.sha256" staged/final.sha256 > staged-delta.json
