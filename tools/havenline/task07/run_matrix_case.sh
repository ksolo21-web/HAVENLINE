#!/usr/bin/env bash
set -euo pipefail

mode=${HAVENLINE_T07_MATRIX_MODE:?HAVENLINE_T07_MATRIX_MODE is required}
godot_bin=${GODOT_BIN:?GODOT_BIN is required}
case "$mode" in
  device)
    test "$#" -eq 3
    state=$1; width=$2; height=$3
    test "$state" = "${HAVENLINE_DEVICE_STATE:?HAVENLINE_DEVICE_STATE is required}"
    python3 - "$state" "$width" "$height" <<'PY'
import json,sys
state,width,height=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
matrix=json.load(open('Docs/Production/DEVICE_LAYOUT_MATRIX.json'))
expected={row['id']:row['logical_size'] for row in matrix['states']}
assert state in expected,(state,sorted(expected))
assert expected[state]==[width,height],(state,expected[state],[width,height])
print(json.dumps({'adapter':'t07-device-v1','state':state,'logical_size':[width,height],'validated':True}))
PY
    suite=test_adaptive_devices
    ;;
  save)
    test "$#" -eq 1
    save_case=$1
    test "$save_case" = "${HAVENLINE_SAVE_CASE:?HAVENLINE_SAVE_CASE is required}"
    python3 - "$save_case" <<'PY'
import json,sys
case=sys.argv[1]
matrix=json.load(open('Docs/Production/SAVE_STATE_MATRIX.json'))
required={row['id'] for row in matrix['cases'] if row['required']}
assert case in required,(case,sorted(required))
print(json.dumps({'adapter':'t07-save-v1','case':case,'validated':True,'context_ephemeral':True}))
PY
    suite=test_crew_and_persistence
    ;;
  *) echo "unknown matrix mode: $mode" >&2; exit 2 ;;
esac

"$godot_bin" --headless --audio-driver Dummy --path HavenlineGodot --script "res://tests/$suite.gd"
