#!/bin/bash
set -eu
expected=9e335e2772d593b3e1f7b9f27f331b36ca8f5283f998018b95c4d769bfda1a61
p=../hvn-c1-owner-right-palm-reauthor-v1
echo "$expected  $p/AUTHOR-SHA256SUMS" | sha256sum -c >&2
(cd "$p" && sha256sum -c AUTHOR-SHA256SUMS >&2)
cp "$p"/{reauthor.py,boundary.py,source.py,run.sh} .
LOCAL_GEOMETRY_NPZ=1 bash run.sh "${1:-/tmp/c1-held-independent.iA3msD/held_owner.npz}" > original-replay.LOCAL.json
cmp original-replay.LOCAL.json "$p"/result.json
bash run_uv.sh "${1:-/tmp/c1-held-independent.iA3msD/held_owner.npz}"
