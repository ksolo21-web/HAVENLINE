#!/usr/bin/env bash
set -euo pipefail
repo="$(realpath "${1:?exact PR checkout}")"
offset="$(realpath "${2:?sealed socket patch directory}")"
basis="$(realpath "${3:?sealed actor-relative patch directory}")"
head=48c6c53a0dfda117ef12c68b32cfe2b3732d5239
test "$(git -C "$repo" rev-parse HEAD)" = "$head"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
git -C "$repo" show "$head:HavenlineLevel1/character_kit.gd" > "$tmp/character_kit.gd"
cd "$tmp"
base=e36c676137882ac5d3e195645b78e30ab6c476fd
mid=201e2bae435b23ba1ce09f9b8fb6f33b56a44cb0
goal=70ca824843c39109868942c234d2475c0e24d0a8
test "$(git hash-object character_kit.gd)" = "$base"
git apply -p2 --check "$offset/socket-offset-only.patch"; git apply -p2 "$offset/socket-offset-only.patch"
test "$(git hash-object character_kit.gd)" = "$mid"
git apply -p1 --check "$basis/held-basis-only.patch"; git apply -p1 "$basis/held-basis-only.patch"
test "$(git hash-object character_kit.gd)" = "$goal"
git apply -p1 -R --check "$basis/held-basis-only.patch"; git apply -p1 -R "$basis/held-basis-only.patch"
test "$(git hash-object character_kit.gd)" = "$mid"
git apply -p2 -R --check "$offset/socket-offset-only.patch"; git apply -p2 -R "$offset/socket-offset-only.patch"
test "$(git hash-object character_kit.gd)" = "$base"
printf 'PASS %s %s -> %s -> %s -> %s -> %s\n' "$head" "$base" "$mid" "$goal" "$mid" "$base"
