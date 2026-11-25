#!/usr/bin/env bash
set -euo pipefail
repo="$(cd "${1:?exact PR108 checkout}" && pwd)"
packet="$(cd "${2:?frozen patch witness}" && pwd)"
head=48c6c53a0dfda117ef12c68b32cfe2b3732d5239
path=HavenlineLevel1/character_kit.gd
base=e36c676137882ac5d3e195645b78e30ab6c476fd
after=201e2bae435b23ba1ce09f9b8fb6f33b56a44cb0
test "$(git -C "$repo" rev-parse HEAD)" = "$head"
(cd "$packet" && test "$(sha256sum SHA256SUMS | cut -d' ' -f1)" = e9e20043c513d616c0f166b758d278fb6cb90a826e85d2c81ed4778a2566e67e && sha256sum -c SHA256SUMS)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/HavenlineLevel1"
git -C "$repo" show "$head:$path" > "$tmp/$path"
git -C "$repo" grep -nE 'Socket_|_palm_l|_palm_r|_sheath' "$head" -- HavenlineLevel1 ':!*.glb'
cd "$tmp"
test "$(git hash-object "$path")" = "$base"
git apply --check "$packet/socket-offset-only.patch"
git apply --numstat "$packet/socket-offset-only.patch"
git apply "$packet/socket-offset-only.patch"
test "$(git hash-object "$path")" = "$after"
test "$(grep -c '_socket_world_transform(_' "$path")" -eq 4
grep -nE 'SOCKET_OFFSET|_socket_world_transform|attachment\.|side \* 0.08' "$path"
git apply -R --check "$packet/socket-offset-only.patch"
git apply -R "$packet/socket-offset-only.patch"
test "$(git hash-object "$path")" = "$base"
printf '%s\n' "PASS $head $base -> $after -> $base"
