#!/usr/bin/env bash
set -euo pipefail

mode=${HAVENLINE_T06_MATRIX_MODE:?HAVENLINE_T06_MATRIX_MODE is required}
godot_bin=${GODOT_BIN:?GODOT_BIN is required}
case "$mode" in
  device) suite=test_adaptive_devices ;;
  save) suite=test_crew_and_persistence ;;
  *) echo "unknown matrix mode: $mode" >&2; exit 2 ;;
esac

"$godot_bin" --headless --audio-driver Dummy --path HavenlineGodot --script "res://tests/$suite.gd"
