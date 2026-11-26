#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
base=$(realpath -e -- "$1")
donor=$(realpath -e -- "$2")
review=$(realpath -e -- "$3")
test "$(sha256sum "$base/SHA256SUMS" | cut -d' ' -f1)" = 439075309ff02a8b78bedee7375a7c2653f74e777b40d2dfe8d8dd66df512fdf
test "$(sha256sum "$donor/SHA256SUMS" | cut -d' ' -f1)" = 349fcbb88c66469cfc50f8c4d2e84249a68a2954378836e78ab9b3f2e19e006c
test "$(sha256sum "$review/SHA256SUMS" | cut -d' ' -f1)" = b3b3ec47a67c102a0e3d04e882e65cd876ed60e1910b57ebeff460696153198d
test "$(sha256sum v2-reference-panel-evidence.json | cut -d' ' -f1)" = 7536559f22d40f9dc1cb8b57e6163b78fb2d83e6ca65729758782422ed7511dc
for d in "$base" "$donor" "$review"; do (cd "$d"; sha256sum -c --status SHA256SUMS); done
(cd "$base/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
q="$p/previews/reference_panel/assets"
# Keep same stock-compatible resource path so route, runtime observer and guard remain byte-exact.
cp "$donor/candidate/Fence18595V3.obj" "$q/Fence18595V2.obj"
rm "$q/Fence18595V2.mtl"
cp "$donor/candidate/Fence18595V3.mtl" "$q/Fence18595V3.mtl"
python3 -B verify_stage.py "$base/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
