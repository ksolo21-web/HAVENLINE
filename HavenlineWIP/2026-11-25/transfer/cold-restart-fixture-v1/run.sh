#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
lock="${1:?Provide existing Havenline Godot geometry/test lock path}"
test -f "$lock"
exec 9<>"$lock"
flock -n 9 || { echo 'Godot lease in use' >&2; exit 1; }
if pgrep -x godot >/dev/null; then echo 'A competing Godot process exists' >&2; exit 1; fi
root="$(mktemp -d /tmp/hvn-transfer-cold-run.XXXXXXXX)"
profiles=()
writer=''
still_writer() { test -n "$writer" && jobs -pr | grep -Fxq -- "$writer"; }
cleanup() {
    if still_writer; then kill -KILL "$writer" || true; wait "$writer" 2>/dev/null || true; fi
    for profile in "${profiles[@]}"; do rm -rf -- "$profile"; done
    rm -rf -- "$root"
}
trap cleanup EXIT
mkdir "$root"/{project,home,config,cache,data,state,tmp}
cp "$here/"{project.godot,planner_upstream.gd,store.gd,commit_fixture.gd,test.gd} "$root/project/"
printf '%s  %s\n' '0ae04e267c01a0163cc29f6eabb23c1d8cc93edb635ced9e865a5452dcde9151' "$root/project/planner_upstream.gd" | sha256sum --check --status
export HOME="$root/home" XDG_CONFIG_HOME="$root/config" XDG_CACHE_HOME="$root/cache" XDG_DATA_HOME="$root/data" XDG_STATE_HOME="$root/state" TMPDIR="$root/tmp"
umask 077
for cut in before after; do
    profile="$(mktemp -d /tmp/hvn-transfer-cold-profile.XXXXXXXX)"
    profiles+=("$profile")
    printf 'DETACHED HAVENLINE TRANSFER COLD FIXTURE V1\n' > "$profile/TRANSFER-FIXTURE-ONLY"
    godot --headless --path "$root/project" --script res://test.gd -- "writer-$cut" "$profile" >"$root/writer.log" 2>&1 &
    writer=$!
    ready="$profile/transfer-fixture-v1.cut-ready"
    for _ in $(seq 1 300); do
        if test -s "$ready" && grep -Fxq -- "$writer writer-$cut" "$ready"; then break; fi
        if ! still_writer; then cat "$root/writer.log"; echo 'writer exited before cut ready' >&2; exit 1; fi
        sleep 0.02
    done
    if ! test -s "$ready" || ! grep -Fxq -- "$writer writer-$cut" "$ready" || ! still_writer; then cat "$root/writer.log"; exit 1; fi
    test -f "$profile/transfer-fixture-v1.primary"
    if test "$cut" = before; then test -f "$profile/transfer-fixture-v1.stage"; else test ! -e "$profile/transfer-fixture-v1.stage"; fi
    primary_before_kill="$(sha256sum "$profile/transfer-fixture-v1.primary" | cut -d ' ' -f 1)"
    stage_before_kill=''
    if test "$cut" = before; then
        stage_before_kill="$(sha256sum "$profile/transfer-fixture-v1.stage" | cut -d ' ' -f 1)"
        test "$primary_before_kill" != "$stage_before_kill"
        pending_digest=$stage_before_kill
    else
        test "$primary_before_kill" = "$pending_digest"
    fi
    kill -KILL "$writer"
    set +e
    wait "$writer" 2>/dev/null
    status=$?
    set -e
    test "$status" -eq 137
    test "$(sha256sum "$profile/transfer-fixture-v1.primary" | cut -d ' ' -f 1)" = "$primary_before_kill"
    if test "$cut" = before; then
        test "$(sha256sum "$profile/transfer-fixture-v1.stage" | cut -d ' ' -f 1)" = "$stage_before_kill"
    fi
    echo "OS cut $cut: PID $writer returned status $status; independently hashed bytes match across kill"

    writer_pid=$writer
    writer=''
    cat "$root/writer.log"
    timeout 30 godot --headless --path "$root/project" --script res://test.gd -- "reader-$cut" "$profile" >"$root/reader.log" 2>&1 || { cat "$root/reader.log"; exit 1; }
    cat "$root/reader.log"
    reader_pid="$(sed -nE 's/^.*"pid":([0-9]+).*$/\1/p' "$root/reader.log")"
    test -n "$reader_pid" && test "$reader_pid" -ne "$writer_pid"
    test -f "$profile/transfer-fixture-v1.primary" && test ! -e "$profile/transfer-fixture-v1.stage"
    test "$(find "$profile" -mindepth 1 -maxdepth 1 -type f | wc -l)" -eq 3
    if test "$cut" = before; then
        test "$(sha256sum "$profile/transfer-fixture-v1.primary" | cut -d ' ' -f 1)" = "$pending_digest"
    else
        test "$(sha256sum "$profile/transfer-fixture-v1.primary" | cut -d ' ' -f 1)" != "$pending_digest"
    fi

done
echo 'Both process-restart cuts PASS (sequential leased Godot, isolated profiles cleaned).'
