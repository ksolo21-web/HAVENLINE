#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
src="${1:?exact owner video 124510 required}"
ref="${2:?reference full-frame directory required}"
native="${3:?exact combined project raw sample directory required}"
echo "4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2  $src" | sha256sum --check --status
t="$(mktemp -d /tmp/hvn-wood-storage-framecheck.XXXXXXXX)"
trap 'rm -rf -- "$t"' EXIT
for ts in 27 27.5 28; do
  ffmpeg -hide_banner -loglevel error -ss "$ts" -i "$src" -frames:v 1 -threads 1 "$t/b$ts-LOCAL.png"
done
OPENBLAS_NUM_THREADS=1 python measure.py "$ref" "$t" "$native"
