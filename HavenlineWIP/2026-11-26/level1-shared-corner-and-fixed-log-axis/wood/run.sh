#!/bin/sh
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
g++ -O3 -shared -fPIC ../hvn-l1-carry-turn-crown-clearance-v1/distance.cpp -o "$tmp/ray.so"
OPENBLAS_NUM_THREADS=1 python -B sweep_axes.py "$tmp/ray.so"
