#!/bin/bash
# Run only under an explicit serial Godot function lease, not a renderer lease.
set -euo pipefail
cd "$(dirname "$0")"
umask 077
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9 || { echo "Godot functional lease held" >&2; exit 75; }
exec 8>/tmp/havenline-pine-storage-fixture-writer.lock
flock -n 8 || { echo "Fixture writer lease held" >&2; exit 75; }
envroot="$(mktemp -d /tmp/hvn-pine-store-engine-env.XXXXXXXX)"
export HOME="$envroot/home" XDG_DATA_HOME="$envroot/data" XDG_CONFIG_HOME="$envroot/config" XDG_CACHE_HOME="$envroot/cache" XDG_RUNTIME_DIR="$envroot/run" TMPDIR="$envroot/tmp"
mkdir -- "$HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" "$TMPDIR"
p="$(bash prepare.sh "${1:-../havenline-tree-regrow.IVOMrj/repo}")"
r="$(mktemp -d "$PWD/runtime.XXXXXXXX")"
pin=e88468b70209be294e23a03b5200dcd60d9a69c71116f77637efbd960935efbd
owner="$(python3 -c 'import secrets;print(secrets.token_hex(16))')"
make_profile() {
  local dir="$(mktemp -d /tmp/havenline-pine-store-fixture-XXXXXXXX)"
  printf 'HAVENLINE-PINE-NATIVE-FIXTURE\n%s\n%s\n' "$pin" "$owner" > "$dir/PINE-STORE-TEST-OWNER"
  printf '%s\n' "$dir"
}
main="$(make_profile)"
aborted="$(make_profile)"
old1="$(make_profile)"
old2="$(make_profile)"
python3 seed.py "$old1" v1
python3 seed.py "$old2" v2
{
  printf '%s\n' "$p"
  printf '%s\n' "$main" "$aborted" "$old1" "$old2" "$envroot"
} > "$r/disposable.LOCAL"
native() {
  local n="$1"; shift
  local code=0
  timeout 180 "${GODOT:-godot}" --headless --path "$p" "$@" > "$r/$n.log" 2>&1 || code=$?
  printf '%s\n' "$code" > "$r/$n.exit"
  if [ "$code" != 0 ] || grep -Eqi '(SCRIPT ERROR|^ERROR:|Parse Error)' "$r/$n.log"; then tail -40 "$r/$n.log" >&2; return 1; fi
}
route() {
  local name="$1" phase="$2" profile="$3" oid="$4"
  native "$name" --script res://fixtures/pine_store/route.gd -- "--pine-store-test-phase=$phase" "--pine-store-fixture=$profile" "--pine-store-owner=$oid"
}
native import --editor --import
route invalid_owner invalid_owner "$main" ffffffffffffffffffffffffffffffff
test ! -e "$main/pine-store-fixture.json"
route native_v1 read_v1 "$old1" "$owner"
route native_v2 read_v2 "$old2" "$owner"
route ordinary_deposit route "$main" "$owner"
route fresh_process_next resume "$main" "$owner"
route failed_stage forced_abort "$aborted" "$owner"
route restart_aborted read_abort "$aborted" "$owner"
printf '%s\n' "$r"
