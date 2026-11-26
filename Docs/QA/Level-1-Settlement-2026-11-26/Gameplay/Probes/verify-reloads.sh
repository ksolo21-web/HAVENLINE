set -eu
p=$(cd -- "$(dirname -- "$0")" && pwd)
g=${HL_GAME_PROJECT:-/workspace/scratch/level1-finish/Game}
r="$1"
for k in level-one-ready post-completion; do
 profile=$(mktemp -d /tmp/havenline-l1-v3-finish-reload-XXXXXXXX)
 echo HAVENLINE-ALFRED-V3-DISPOSABLE > "$profile/L1-DISPOSABLE"
 cp "$r/$k.save.json" "$profile/field-inventory-v1.json"
 export HL_EXPECT_LEVEL=1
 if test "$k" = post-completion; then HL_EXPECT_LEVEL=2; fi
 export HL_RELOAD_JSON="$r/$k-reload.json" XDG_DATA_HOME="$profile/data" XDG_CACHE_HOME="$profile/cache" XDG_CONFIG_HOME="$profile/config"
 godot --path "$g" --headless --audio-driver Dummy --fixed-fps 60 --script "$p/reload.gd" -- "--l1-disposable-profile=$profile" > "$r/$k-reload.log" 2>&1
done
