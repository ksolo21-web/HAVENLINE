#!/usr/bin/env bash
set -euo pipefail
test "${1:-}" = --root-granted-functional-lease
here=$(cd -- "$(dirname "$0")" && pwd -P)
engine=/opt/godot/4.7.2/Godot_v4.7.2-stable_linux.x86_64
test -x "$engine"
exec 9>/tmp/havenline-godot-headless.lock
flock -n 9
! ps -u "$(id -u)" -o comm= | grep -qi '^godot'
out=$(mktemp -d "$here/run.XXXXXXXX")
w=$(mktemp -d /tmp/hvn-pine-rollback-project.XXXXXXXX)
candidate_profile=""
v1_profile=""
v2_profile=""
clean(){ local p; for p in "$w" "$candidate_profile" "$v1_profile" "$v2_profile"; do [[ -z "$p" ]] || rm -rf -- "$p"; done; }
trap clean EXIT
candidate_profile=$(mktemp -d /tmp/havenline-l1-v3-pine-rollback-candidate-XXXXXXXX)
v1_profile=$(mktemp -d /tmp/havenline-l1-v3-pine-rollback-oldv1-XXXXXXXX)
v2_profile=$(mktemp -d /tmp/havenline-l1-v3-pine-rollback-oldv2-XXXXXXXX)
for p in "$candidate_profile" "$v1_profile" "$v2_profile"; do
  printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$p/L1-DISPOSABLE"
done
printf 'PINE-ROLLBACK-CANDIDATE-V1\n' > "$candidate_profile/PINE-ROLLBACK-CANDIDATE"
printf 'PINE-ROLLBACK-LEGACY-v1\n' > "$v1_profile/PINE-ROLLBACK-LEGACY"
printf 'PINE-ROLLBACK-LEGACY-v2\n' > "$v2_profile/PINE-ROLLBACK-LEGACY"
(cd "$here/staged"; sha256sum -c --status content.sha256)
cp -a "$here/staged"/{HavenlineLevel1,legacy} "$w/"
(cd "$w"; sha256sum -c --status "$here/staged/content.sha256")
run(){ local phase=$1 project=$2; shift 2; local p="$w/env-$phase"
  mkdir -m700 -p "$p"/{home,xdata,xconfig,xcache,xstate,xruntime,tmp}
  timeout 180 env HOME="$p/home" XDG_DATA_HOME="$p/xdata" XDG_CONFIG_HOME="$p/xconfig" XDG_CACHE_HOME="$p/xcache" XDG_STATE_HOME="$p/xstate" XDG_RUNTIME_DIR="$p/xruntime" TMPDIR="$p/tmp" \
    "$engine" --headless --path "$project" "$@" > "$out/$phase.log" 2>&1
  grep -q '^Godot Engine v4\.7\.2\.stable\.official\.' "$out/$phase.log"
  if [[ "$phase" = import ]]; then
    local obj="^WARNING: OBJ: Ambient light for material '(board|board_warm|board_soft|beam|brace_back|snow|metal|rope|rope_dark)' is ignored in PBR$"
    test "$(grep -Ec "$obj" "$out/$phase.log")" -eq 18
    ! grep -Ei '(ERROR|WARNING):|Parse Error' "$out/$phase.log" | grep -Ev "$obj"
  else
    ! grep -Ei '(ERROR|WARNING):|Parse Error|^FAIL' "$out/$phase.log"
  fi
}
run import "$w/HavenlineLevel1" --editor --import --quit
run candidate "$w/HavenlineLevel1" --fixed-fps 60 --script res://tests/pine_rollback_candidate.gd -- "--l1-disposable-profile=$candidate_profile" --hvn-pine-rollback-candidate
grep -E '^PINE_ROLLBACK_CANDIDATE checks=[1-9][0-9]* failures=0$' "$out/candidate.log"
python "$here/validate_payload.py" "$candidate_profile" > "$out/writer-digests.json"
cp "$candidate_profile/v1-frozen.json" "$v1_profile/opening-v3.json"
cp "$candidate_profile/opening-v3.json" "$v2_profile/opening-v3.json"
cmp "$candidate_profile/v1-frozen.json" "$v1_profile/opening-v3.json"
cmp "$candidate_profile/opening-v3.json" "$v2_profile/opening-v3.json"
profile_snap(){ local dir=$1; (
  cd "$dir"
  find . -mindepth 1 -maxdepth 1 -printf '%y %m %P\n' | sort
  find . -mindepth 1 -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum
); }
for mode in v1 v2; do
  phase="legacy-$mode"
  profile=$v1_profile
  [[ "$mode" != v2 ]] || profile=$v2_profile
  test -z "$(find "$profile" -mindepth 1 -maxdepth 1 ! -type f -print -quit)"
  test "$(find "$profile" -mindepth 1 -maxdepth 1 -type f | wc -l)" -eq 3
  profile_snap "$profile" > "$out/$phase.before"
  run "$phase" "$w/legacy" --script res://legacy.gd -- "--l1-disposable-profile=$profile" "--hvn-pine-rollback-old=$mode"
  grep -E "^PINE_ROLLBACK_LEGACY mode=$mode checks=[1-9][0-9]* failures=0$" "$out/$phase.log"
  profile_snap "$profile" > "$out/$phase.after"
  cmp "$out/$phase.before" "$out/$phase.after"
done
cmp "$candidate_profile/v1-frozen.json" "$v1_profile/opening-v3.json"
cmp "$candidate_profile/opening-v3.json" "$v2_profile/opening-v3.json"
find "$w" -type f -name 'opening-v3.*' -print > "$out/no_unexpected_save_paths"
test ! -s "$out/no_unexpected_save_paths"
(cd "$w"; sha256sum -c --status "$here/staged/content.sha256")
(cd "$here/staged"; sha256sum -c --status content.sha256)
printf '%s\n' "$out"
