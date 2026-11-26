#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname "$0")" && pwd -P)
repo=$(realpath "$1")
author=$(realpath "$2")
pin=11c14a1c41971067c7dc97db69375f720a408f68
tree=d764a05246cbff96983aa27af17e2e919a946ae0
test "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1")" = "$tree"
test "$(sha256sum "$author/SHA256SUMS" | cut -d' ' -f1)" = 2939ea7d5a82461840888791619fd4ecc0eb41d6f6371cfc4170554de94d5a2f
(cd "$author"; sha256sum -c --status SHA256SUMS)
test "$(sha256sum "$author/renewal.patch" | cut -d' ' -f1)" = e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd
test ! -e "$here/staged"
mkdir -p "$here/staged"/{old,new/HavenlineLevel1,read-only-old}
p="$here/staged"
git -C "$repo" archive "$pin:HavenlineLevel1" | tar -x -C "$p/old"
while IFS= read -r name; do test "$(git hash-object --no-filters "$p/old/$name")" = "$(git -C "$repo" rev-parse "$pin:HavenlineLevel1/$name")"; done < <(git -C "$repo" ls-tree -r --name-only "$pin:HavenlineLevel1")
test "$(find "$p/old" -type f | wc -l)" -eq 126
test -z "$(find "$p/old" -type l -print -quit)"
python3 "$p/old/tools/hydrate_assets.py"
cp -a "$p/old/." "$p/new/HavenlineLevel1/"
(cd "$p/new"; git apply --check "$author/renewal.patch"; git apply "$author/renewal.patch")
test "$(sha256sum "$p/new/HavenlineLevel1/opening_ledger.gd" | cut -d' ' -f1)" = a65fa1f6fdfa9f304550fe923cc5c14f3d79e6f7b38d59d8441a194caff28e90
test "$(sha256sum "$p/new/HavenlineLevel1/previews/integrated_opening.gd" | cut -d' ' -f1)" = 902eaf6f24356f9a85762888e409eb753e05bd65614d6931c57c796d0bb8f3f4
test "$(sha256sum "$p/new/HavenlineLevel1/tests/paid_pine_spy.gd" | cut -d' ' -f1)" = 9f5454f6d6e92db50b4696caa2a9cff9aaee0dcb647d6332acd411261f52cbb6
test "$(sha256sum "$p/new/HavenlineLevel1/tests/test_paid_pine_renewal.gd" | cut -d' ' -f1)" = e2dcad7478dfe920637e4d97a37a71bb6786f9aca82159306f5ceb57114f4c33
cp "$here/paid_fork.gd" "$p/new/HavenlineLevel1/tests/hvn_pine_profile_fork.gd"
cp "$p"/old/{opening_ledger.gd,opening_save.gd} "$p/read-only-old/"
cp "$here/old_read.gd" "$p/read-only-old/"
printf '%s\n' 'config_version=5' '[application]' 'config/name="Pine fork old read only QA"' '[rendering]' 'renderer/rendering_method="gl_compatibility"' > "$p/read-only-old/project.godot"
(cd "$p"; find old new read-only-old -type f -print0 | sort -z | xargs -0 sha256sum) > "$p/content.sha256"
