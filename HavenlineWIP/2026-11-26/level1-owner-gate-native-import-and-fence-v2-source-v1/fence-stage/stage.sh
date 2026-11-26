#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname "$0")"
base=../hvn-l1-reference-panel-v3-cap-native-preflight-v1
donor=../hvn-l1-fence-owner-33036-separated-v2
review=../hvn-33036-v2-independent
for pin in "$base:d352e28408a87328d6a1ceec1fabe6f3c21eac5c37c2a9c0623ca9f04208d829" "$donor:d1a62ff353863c0844d3d6fcdc4f758e62399d28e8ddab6a1f91267a254ed174" "$review:1a87e626fb3049ed220eb1b29e40bee8a322999753b2e71d3e17401687defcf3"; do
 d=${pin%:*}; test "$(sha256sum "$d/SHA256SUMS"|cut -d' ' -f1)" = "${pin#*:}"; (cd "$d"; sha256sum -c --status SHA256SUMS)
done
test ! -e staged
mkdir staged
cp -a "$base/staged/HavenlineLevel1" staged/
p=staged/HavenlineLevel1
(cd "$p"; sha256sum -c --status "../../$base/staged/draw-source.sha256")
q="$p/previews/reference_panel/assets"
rm "$q"/Fence18595V{2.obj,3.mtl}
cp "$donor"/candidate/FenceOwner33036V2.{obj,mtl} "$q/"
python3 -B adapt.py "$base/staged/HavenlineLevel1" "$p" > stage-evidence.json
(cd "$p"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/draw-source.sha256
