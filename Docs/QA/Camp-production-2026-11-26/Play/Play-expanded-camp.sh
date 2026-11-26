#!/bin/sh
# Open the earned camp in a new disposable profile on each launch.
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
binary=${1:-"$here/Havenline-Level-1.x86_64"}
if [ ! -x "$binary" ]; then
    echo "Extract the Linux game into this folder, or pass the path to its executable." >&2
    exit 1
fi
profile=$(mktemp -d /tmp/havenline-l1-v3-camp-play-XXXXXXXX)
echo HAVENLINE-ALFRED-V3-DISPOSABLE > "$profile/L1-DISPOSABLE"
cp "$here/Expanded-camp.save.json" "$profile/field-inventory-v1.json"
export XDG_DATA_HOME="$profile/data" XDG_CONFIG_HOME="$profile/config" XDG_CACHE_HOME="$profile/cache"
printf 'Expanded camp playtest in %s\n' "$profile"
exec "$binary" -- "--l1-disposable-profile=$profile"
