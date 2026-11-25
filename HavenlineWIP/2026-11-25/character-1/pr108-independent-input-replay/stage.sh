#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
checkout="$(realpath "${1:?provide pinned sparse read-only checkout}")"
lease="${2:?provide already-existing admitted serial Havenline lease}"
test -f "$lease"
test "$(git -C "$checkout" rev-parse HEAD)" = 48c6c53a0dfda117ef12c68b32cfe2b3732d5239
# Only read exact files as checked out; tracked changes (including staged) deny admission.
test -z "$(git -C "$checkout" status --porcelain --untracked-files=no -- HavenlineLevel1)"
for path in assets/characters/Character1.glb assets/tools/axe.glb assets/tools/pickaxe.glb; do
 actual="$(git hash-object --no-filters "$checkout/HavenlineLevel1/$path")"
 test "$actual" = "$(git -C "$checkout" rev-parse "HEAD:HavenlineLevel1/$path")"
done
exec 9<>"$lease"
flock -n 9
if pgrep -x godot >/dev/null; then echo 'Competing Godot process present' >&2; exit 2; fi
root="$(mktemp -d /tmp/hvn-pr108-input.XXXXXXXX)"
trap 'rm -rf "$root"' EXIT
mkdir "$root/"{project,home,config,cache,data,state,runtime,tmp}
chmod 700 "$root/runtime"
git -C "$checkout" archive HEAD:HavenlineLevel1 | tar xf - -C "$root/project"
export HOME="$root/home" XDG_CONFIG_HOME="$root/config" XDG_CACHE_HOME="$root/cache"
export XDG_DATA_HOME="$root/data" XDG_STATE_HOME="$root/state" XDG_RUNTIME_DIR="$root/runtime" TMPDIR="$root/tmp"
unset DISPLAY WAYLAND_DISPLAY
python3 "$root/project/tools/hydrate_assets.py"
env timeout 120 godot --headless --path "$root/project" --editor --import --quit
cp "$here/regression.gd" "$root/project/regression.gd"
env timeout 60 godot --headless --path "$root/project" --script res://regression.gd
