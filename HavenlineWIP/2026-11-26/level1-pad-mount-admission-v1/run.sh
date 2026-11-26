#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} != "--root-granted-functional-lease" ]]; then
  echo 'This test requires the root coordinator to grant the sole functional engine lease.' >&2
  exit 2
fi
here=$(cd "$(dirname "$0")" && pwd -P)
readonly godot=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
readonly observer=res://tests/observe_purchase_mounts.gd
readonly stock_fixture=--l1-enable-combined-cold-fixture
readonly opt_in=--hvn-observe-purchase-mounts
test -x "$godot"
test -z "$(pgrep -f '^(/opt/godot/4[.]7[.]2/Godot_v4[.]7[.]2-stable_linux[.]x86_64|([^ ]*/)?godot4?)( |$)' || true)"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
test -z "$(pgrep -f '^(/opt/godot/4[.]7[.]2/Godot_v4[.]7[.]2-stable_linux[.]x86_64|([^ ]*/)?godot4?)( |$)' || true)"
(cd "$here/project" && sha256sum -c --status "$here/staged-source.sha256")
out=$(mktemp -d "$here/run.XXXXXXXX")
a=$(mktemp -d /tmp/havenline-l1-v3-combined-admission-paid-XXXXXXXX)
b=$(mktemp -d /tmp/havenline-l1-v3-combined-admission-fail-XXXXXXXX)
trap 'rm -rf -- "$a" "$b"' EXIT
for p in "$a" "$b"; do
  printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$p/L1-DISPOSABLE"
  printf 'HAVENLINE-COMBINED-COLD-V1\n' > "$p/COMBINED-COLD-FIXTURE"
done
cp -a -- "$here/project" "$out/project"
profile() {
  local mode=$1; shift
  local p="$out/$mode"
  mkdir -p -- "$p"/{home,data,cache,config,state,runtime,tmp}
  chmod 700 "$p/runtime"
  timeout 115s env HOME="$p/home" XDG_DATA_HOME="$p/data" XDG_CACHE_HOME="$p/cache" XDG_CONFIG_HOME="$p/config" XDG_STATE_HOME="$p/state" XDG_RUNTIME_DIR="$p/runtime" TMPDIR="$p/tmp" \
    "$godot" --headless --path "$out/project" "$@" > "$p/log" 2>&1
  # These exact ambient-OBJ annotations are from importing the untouched
  # legacy gate MTL assets. No allowlist applies to any runtime phase.
  local diag='(^| )(ERROR|WARNING):'
  local obj="^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$"
  if [[ "$mode" == import ]]; then
    test "$(grep -Ec "$obj" "$p/log")" -eq 18
  else
    obj='^UNEXPECTED_ALLOWLIST_DISABLED$'
  fi
  if grep -Ei "$diag" "$p/log" | grep -Ev "$obj"; then
    echo "unexpected engine diagnostic in $p/log" >&2
    return 1
  fi
}
profile import --editor --import --quit
grep -F 'Godot Engine v4.7.2' "$out/import/log"
phase() {
  local key=$1 path=${2:-}
  local flags=()
  [[ -z "$path" ]] || flags=("$stock_fixture" "--l1-disposable-profile=$path")
  profile "$key" --fixed-fps 60 --script "$observer" -- "$opt_in" "--phase=$key" "${flags[@]}"
  grep -E '^purchase mount admission checks=[1-9][0-9]* failures=0$' "$out/$key/log"
}
phase default
phase write "$a"
test -f "$a/opening-v3.json"
test ! -e "$a/opening-v3.stage"
phase cold "$a"
phase fail "$b"
test -f "$b/opening-v3.json"
test -d "$b/opening-v3.stage"
phase recover "$b"
(cd "$out/project" && sha256sum -c --status "$here/staged-source.sha256")
(cd "$here/project" && sha256sum -c --status "$here/staged-source.sha256")
printf '%s\n' "$out"
