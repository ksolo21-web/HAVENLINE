#!/bin/bash
# Only under an explicitly granted serial Godot functional lease.
set -euo pipefail
cd "$(dirname "$0")"
engine="${GODOT:-godot}"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9 || { echo "Godot lease lock already held" >&2; exit 75; }
sandbox="$(mktemp -d /tmp/hvn-paid-pine-env.XXXXXXXX)"
export HOME="$sandbox/home" XDG_DATA_HOME="$sandbox/data" XDG_CONFIG_HOME="$sandbox/config" XDG_CACHE_HOME="$sandbox/cache" XDG_RUNTIME_DIR="$sandbox/runtime" TMPDIR="$sandbox/tmp"
mkdir -m 700 -- "$HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" "$TMPDIR"
project="$(bash prepare.sh "${1:-../havenline-tree-regrow.IVOMrj/repo}")"
out="$(mktemp -d "$PWD/runtime.XXXXXXXX")"
profile="$(mktemp -d /tmp/havenline-l1-v3-pine.XXXXXXXX)"
# save.configure requires an alphanumeric/hyphen/underscore leaf.
valid_profile="${profile/./-}"
mv "$profile" "$valid_profile"
profile="$valid_profile"
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
printf '%s\n' "$project" "$profile" > "$out/paths.LOCAL"
command_status(){
  local name="$1"; shift
  set +e
  timeout 180 "$engine" --headless --path "$project" "$@" > "$out/$name.log" 2>&1
  code=$?
  printf '%d\n' "$code" > "$out/$name.exit"
  set -e
  if [ "$code" -ne 0 ]; then tail -25 "$out/$name.log" >&2; return "$code"; fi
  if grep -Eq '(SCRIPT ERROR|^ERROR:|Parse Error)' "$out/$name.log"; then tail -25 "$out/$name.log" >&2; return 1; fi
}
command_status import --editor --import
command_status nostalgic --script res://tests/test_integrated_tree_regrowth.gd
command_status late_payment --script res://tests/test_paid_pine_renewal.gd -- --pine-case=settle_after_buy
command_status restored_route_first --script res://tests/test_paid_pine_renewal.gd -- "--l1-disposable-profile=$profile" --pine-case=route
command_status restored_cold --script res://tests/test_paid_pine_renewal.gd -- "--l1-disposable-profile=$profile" --pine-case=recover
printf '%s\n' "$out"
