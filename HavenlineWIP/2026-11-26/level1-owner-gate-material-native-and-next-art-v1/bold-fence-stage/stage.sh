#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
base=../hvn-l1-fence-owner-33036-v2-native-profile-fix-v1
donor=../hvn-l1-fence-33036-bold-wrap-v3
review=../hvn-33036-v3-bold-independent
for pin in "$base:80bbeb4d397fa739b8763a30106ac569d0d85865c8fdfb0724bf844c6dc87777" "$donor:f8a0739c1bda8d64fed39988ff5c12bf7234c64f4066962b887df331fa4470f1" "$review:77d78496e0f9cba8894e4930802febc3c7d177b0ab13af9d7a8eca6afad815ff"; do
 d=${pin%:*}; test "$(sha256sum "$d/SHA256SUMS"|cut -d' ' -f1)" = "${pin#*:}"; (cd "$d"; sha256sum -c --status SHA256SUMS)
done
test "$(sha256sum prior-panel-evidence.json|cut -d' ' -f1)" = 519b1eca453a58e29199ba1634214725e26bea673e1ae9b7d10e9bb736faf285
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
(cd "$p"; sha256sum -c --status "../../$base/staged/draw-source.sha256")
q="$p/previews/reference_panel/assets"
rm "$q"/FenceOwner33036V2.{obj,mtl}
cp "$donor"/candidate/FenceOwner33036BoldWrapV3.{obj,mtl} "$q/"
python3 -B adapt.py "$base/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
