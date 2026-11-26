#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/havenline-level1-settlement-trial"
exec "$app_dir/Havenline-Level-1.x86_64" "$@"
