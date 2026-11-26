#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd -P)
repo="$here/isolated-source"
project="$here/project"
revision=11c14a1c41971067c7dc97db69375f720a408f68
test "$(git -C "$repo" rev-parse HEAD)" = "$revision"
test "$(git -C "$repo" rev-parse HEAD:HavenlineLevel1)" = d764a05246cbff96983aa27af17e2e919a946ae0
test -z "$(git -C "$repo" status --porcelain --untracked-files=all -- HavenlineLevel1)"
test ! -e "$project"
mkdir "$project"
git -C "$repo" archive "$revision:HavenlineLevel1" | tar -x -C "$project"
test "$(wc -l < "$here/source-git-blobs.txt")" -eq 126
test "$(find "$project" -type f | wc -l)" -eq 126
while IFS=' ' read -r hash name; do
  test "$(git -C "$repo" hash-object --no-filters "$project/$name")" = "$hash"
done < "$here/source-git-blobs.txt"
python3 "$project/tools/hydrate_assets.py"
test ! -e "$project/tests/observe_purchase_mounts.gd"
cp "$here/observe_purchase_mounts.gd" "$project/tests/observe_purchase_mounts.gd"
(
  cd "$project"
  find . -type f -print0 | sort -z | xargs -0 sha256sum
) > "$here/staged-source.sha256"
