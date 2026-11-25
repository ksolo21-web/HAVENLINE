#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
root="$PWD"
repo="$(realpath "${1:-../havenline-tree-regrow.IVOMrj/repo}")"
pine="$root/../hvn-l1-paid-pine-renewal-v1/renewal.patch"
posix="$root/../hvn-l1-pine-storage-durable-backend-v1"
indep="$root/../hvn-l1-paid-pine-independent-v1.ILpLHK"
echo "e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd  $pine" | sha256sum -c --status
echo "c52e1ccf7bd332724d16569a270929f14c9e2994f5ab07c0fc7da401b99132bb  $posix/SHA256SUMS" | sha256sum -c --status
(cd "$posix" && sha256sum -c --status SHA256SUMS)
echo "f4ca5871f9d30c8be7c6a186a96ed8ef9d5912042336b70e6ee0d03c75b8393b  $indep/SHA256SUMS" | sha256sum -c --status
(cd "$indep" && sha256sum -c --status SHA256SUMS)
sha=11c14a1c41971067c7dc97db69375f720a408f68
dest="$(mktemp -d "$root/native.XXXXXXXX")"
git -C "$repo" archive "$sha" HavenlineLevel1 | tar -x -C "$dest"
p="$dest/HavenlineLevel1"
studio="$p/assets/studio"
cat "$studio/parts/hearth_trial_02.part00" "$studio/parts/hearth_trial_02.part01" "$studio/parts/hearth_trial_02.part02" > "$studio/hearth_trial_02.glb"
echo "35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a  $studio/hearth_trial_02.glb" | sha256sum -c --status
(cd "$dest" && git apply --check --whitespace=error "$pine" "$root/fixture.patch" && git apply "$pine" "$root/fixture.patch")
python3 "$root/source_seam.py" "$p"
printf '%s\n' "$p"
