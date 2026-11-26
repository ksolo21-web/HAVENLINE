#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
# All pre-existing files are pinned and remain unchanged. New scene can only run explicitly.
bash stage.sh "$@"
p=staged/HavenlineLevel1
q="$p/previews/r17_fence"
mkdir -p "$q/assets"
cp r17_fence_view.gd r17_fence_view.tscn "$q/"
cp assets/* "$q/assets/"
(cd "$p"; sha256sum -c --status ../final.sha256)
test "$(find "$p" -type f | wc -l)" -eq 136
python3 -B verify_static.py "$p" > custody/static.json
