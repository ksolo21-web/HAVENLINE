#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
base=$(realpath -e -- "$1")
donor=$(realpath -e -- "$2")
independent=$(realpath -e -- "$3")
test "$(sha256sum "$base/SHA256SUMS" | cut -d' ' -f1)" = 95c5d7caef357197dd23c3f4e84a387294125a1882e3c2a5359c87b5b0d73876
test "$(sha256sum "$donor/SHA256SUMS" | cut -d' ' -f1)" = 47f0cfbe91029f2c0d1a43a60ceec2d11f2f8b40c4f48313994076ff3013fff4
(cd "$base"; sha256sum -c --status SHA256SUMS)
(cd "$donor"; sha256sum -c --status SHA256SUMS)
(cd "$base/staged/HavenlineLevel1"; sha256sum -c --status ../draw-source.sha256)
python3 -B verify_inputs.py "$donor" > donor-source-census.json
test -f verify_review.py || { echo "HOLD: exact independent rope-contact receipt not yet authenticated." >&2; exit 24; }
python3 -B verify_review.py "$independent" > independent-receipt.json
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
q="$p/previews/reference_panel"
rm "$q/assets/fence_reference_detail.obj" "$q/assets/reference_detail.mtl"
cp "$donor/candidate/"{Fence18595V2.obj,Fence18595V2.mtl} "$q/assets/"
cp reference_panel.gd "$q/"
python3 -B adapt_v1_observer.py "$p/tests/hvn_l1_combined_draw.gd"
python3 -B verify_stage_delta.py "$base/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
