#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
p=$(realpath -e -- "$1")
test "$(sha256sum "$p/SHA256SUMS" | cut -d' ' -f1)" = 4049ec37b2ab0c7176593d969e286ef673950e506a2d47d8870900e72b9219a9
(cd "$p"; sha256sum -c --status SHA256SUMS)
test ! -e staged
mkdir -p staged
cp -a "$p/staged/HavenlineLevel1" staged/
project=staged/HavenlineLevel1
(cd "$project"; sha256sum -c --status "$p/staged/draw-source.sha256")
mkdir "$project/previews/timber_gate"
cp timber_gate_view.{gd,tscn} "$project/previews/timber_gate/"
test "$(find "$project" -type f | wc -l)" -eq 139
python3 -B verify_static.py "$project" > custody/static.json
(cd "$project"; sha256sum -c --status "$p/staged/draw-source.sha256")
(cd "$project"; find . -type f -print0 | sort -z | xargs -0 sha256sum) > staged/combined.sha256
