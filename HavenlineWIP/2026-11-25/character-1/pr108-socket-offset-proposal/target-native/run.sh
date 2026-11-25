#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
checkout="$(realpath "${1:?exact PR108 checkout}")"
packet="$(realpath "${2:?exact frozen patch directory}")"
lease="${3:?existing serial Godot lease}"; test -f "$lease"
head=48c6c53a0dfda117ef12c68b32cfe2b3732d5239
test "$(git -C "$checkout" rev-parse HEAD)" = "$head"
(cd "$packet" && test "$(sha256sum SHA256SUMS | cut -d' ' -f1)" = e9e20043c513d616c0f166b758d278fb6cb90a826e85d2c81ed4778a2566e67e && sha256sum -c SHA256SUMS)
exec 9<>"$lease"; flock -n 9
if pgrep -x godot >/dev/null; then echo "Godot busy" >&2; exit 2; fi
tmp="$(mktemp -d /tmp/hvn-pr108-target-offset.XXXXXXXX)"
trap 'rm -rf "$tmp"' EXIT
unset DISPLAY WAYLAND_DISPLAY
for variant in original offset-only; do
 r="$tmp/$variant"
 mkdir -p "$r"/{project,home,config,cache,data,state,runtime,tmp}
 chmod 700 "$r/runtime"
 git -C "$checkout" archive "$head:HavenlineLevel1" | tar xf - -C "$r/project"
 (
  cd "$r/project"
  test "$(git hash-object character_kit.gd)" = e36c676137882ac5d3e195645b78e30ab6c476fd
  test "$(git hash-object assets/characters/Character1.glb)" = 9d11c756195ffaac649b7f4c01d80f29d50dfec1
  if [[ "$variant" == offset-only ]]; then
   git apply -p2 --check "$packet/socket-offset-only.patch"
   git apply -p2 "$packet/socket-offset-only.patch"
   test "$(git hash-object character_kit.gd)" = 201e2bae435b23ba1ce09f9b8fb6f33b56a44cb0
  fi
  cp "$here/witness.gd" .
  export HOME="$r/home" XDG_CONFIG_HOME="$r/config" XDG_CACHE_HOME="$r/cache" XDG_DATA_HOME="$r/data" XDG_STATE_HOME="$r/state" XDG_RUNTIME_DIR="$r/runtime" TMPDIR="$r/tmp"
  python3 tools/hydrate_assets.py
  timeout 120 godot --headless --path . --editor --import --quit
  timeout 45 godot --headless --path . --script res://witness.gd -- "$variant"
 )
done
