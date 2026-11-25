#!/bin/bash
# Materialize only in this WIP; never change the source git repository.
set -euo pipefail
cd "$(dirname "$0")"
repo="$(realpath "${1:-../havenline-tree-regrow.IVOMrj/repo}")"
dest="$(mktemp -d "$PWD/native-scene.XXXXXXXX")"
sha=11c14a1c41971067c7dc97db69375f720a408f68
check() { test "$(git -C "$repo" rev-parse "$sha:HavenlineLevel1/$1")" = "$2"; }
check opening_ledger.gd 873def40c950279b210e2b2d0bed5d85625ea189
check previews/integrated_opening.gd cc54fb10b5270f513baa2c3743d4879e29ebb41a
check opening.gd 8de9499b0a48d920516d3b07c889cfb8a0808038
check resource_tree.gd a0a846551bb574728cedcd3b76bfe785cd0b5192
check opening_save.gd 7ba67c0919048ee1c7396a6ef42cb8ec5de99d24
check project.godot 8f6b327bfff760c44c3223a1aa79234f644abdd4
check previews/integrated_opening.tscn 39180754353c4f73355f253dc4d9cb7e1427d1c1
git -C "$repo" archive "$sha" HavenlineLevel1 | tar -x -C "$dest"
studio="$dest/HavenlineLevel1/assets/studio"
cat "$studio/parts/hearth_trial_02.part00" "$studio/parts/hearth_trial_02.part01" "$studio/parts/hearth_trial_02.part02" > "$studio/hearth_trial_02.glb"
printf "35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a  %s\n" "$studio/hearth_trial_02.glb" | sha256sum --check --status
(cd "$dest" && git apply --check "$OLDPWD/renewal.patch" && git apply "$OLDPWD/renewal.patch")
printf '%s\n' "$dest/HavenlineLevel1"
