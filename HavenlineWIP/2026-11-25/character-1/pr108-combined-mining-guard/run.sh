#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
checkout="$(realpath "${1:?provide pinned sparse read-only checkout}")"
lease="${2:?provide already-existing admitted serial Havenline lease}"
mode="${3:?use baseline or repaired}"
[[ "$mode" == baseline || "$mode" == repaired ]]
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
test "$(git hash-object --no-filters "$root/project/opening.gd")" = 6a0f08cffba3d8cacea506e9150e44298e3bc394
if [[ "$mode" == repaired ]]; then
 (cd "$root/project" && git apply --check "$here/combined-only.patch" && git apply "$here/combined-only.patch")
 test "$(git hash-object --no-filters "$root/project/opening.gd")" = "$(cat "$here/patched-opening.git-blob")"
fi
export HOME="$root/home" XDG_CONFIG_HOME="$root/config" XDG_CACHE_HOME="$root/cache"
export XDG_DATA_HOME="$root/data" XDG_STATE_HOME="$root/state" XDG_RUNTIME_DIR="$root/runtime" TMPDIR="$root/tmp"
unset DISPLAY WAYLAND_DISPLAY
python3 "$root/project/tools/hydrate_assets.py"
env timeout 120 godot --headless --path "$root/project" --editor --import --quit
for probe in wall repeat; do
 echo "BEGIN $mode $probe"
 cp "$here/$probe.gd" "$root/project/$probe.gd"
 env timeout 60 godot --headless --path "$root/project" --script "res://$probe.gd" -- "$mode"
 echo "END $mode $probe"
done
