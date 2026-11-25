#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
checkout="$(realpath "${1:?exact PR108 checkout}")"
packet="$(realpath "${2:?exact frozen patch directory}")"
basis="$(realpath "${3:?sealed actor-relative basis patch}")"
lease="${4:?existing serial Godot lease}"; test -f "$lease"
head=48c6c53a0dfda117ef12c68b32cfe2b3732d5239
test "$(git -C "$checkout" rev-parse HEAD)" = "$head"
(cd "$packet" && test "$(sha256sum SHA256SUMS | cut -d' ' -f1)" = e9e20043c513d616c0f166b758d278fb6cb90a826e85d2c81ed4778a2566e67e && sha256sum -c SHA256SUMS)
(cd "$basis" && test "$(sha256sum SHA256SUMS | cut -d' ' -f1)" = 430d5b01a50742fd1af9e695969813666c2fa744b296127038daf79dc50a14fa && sha256sum -c SHA256SUMS)
exec 9<>"$lease"; flock -n 9
if pgrep -x godot >/dev/null; then echo "Godot busy" >&2; exit 2; fi
tmp="$(mktemp -d /tmp/hvn-pr108-dual-patch-yaw.XXXXXXXX)"
trap 'rm -rf "$tmp"' EXIT
unset DISPLAY WAYLAND_DISPLAY
mkdir -p "$tmp"/{project,home,config,cache,data,state,runtime,tmp}
chmod 700 "$tmp/runtime"
git -C "$checkout" archive "$head:HavenlineLevel1" | tar xf - -C "$tmp/project"
cd "$tmp/project"
for pin in \
 e36c676137882ac5d3e195645b78e30ab6c476fd:character_kit.gd \
 9d11c756195ffaac649b7f4c01d80f29d50dfec1:assets/characters/Character1.glb \
 9d7ab5e3cbb42f64b3ce0451e6e5171954dc172e:assets/tools/axe.glb \
 f6e12004a1bcc261df842f3dc758fdabd4cd269f:assets/tools/pickaxe.glb \
 e075b7bb6cb824a853e3b81b4bdadd6fc9f886bb:assets/characters/character1_sockets.json; do
 test "$(git hash-object "${pin#*:}")" = "${pin%%:*}"
done
git apply -p2 --check "$packet/socket-offset-only.patch"
git apply -p2 "$packet/socket-offset-only.patch"
test "$(git hash-object character_kit.gd)" = 201e2bae435b23ba1ce09f9b8fb6f33b56a44cb0
git apply -p1 --check "$basis/held-basis-only.patch"
git apply -p1 "$basis/held-basis-only.patch"
test "$(git hash-object character_kit.gd)" = 70ca824843c39109868942c234d2475c0e24d0a8
cp "$here/yaw_probe.gd" .
export HOME="$tmp/home" XDG_CONFIG_HOME="$tmp/config" XDG_CACHE_HOME="$tmp/cache" XDG_DATA_HOME="$tmp/data" XDG_STATE_HOME="$tmp/state" XDG_RUNTIME_DIR="$tmp/runtime" TMPDIR="$tmp/tmp"
python3 tools/hydrate_assets.py
timeout 120 godot --headless --path . --editor --import --quit >&2
timeout 45 godot --headless --path . --script res://yaw_probe.gd
