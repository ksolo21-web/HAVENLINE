set -eu
project=$1
variant=$2
fixture="$3"
shift 3
out=/tmp/havenline-t05-wide/$variant
mkdir -p "$out"
p=$(mktemp -d /tmp/havenline-l1-v3-goods-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$p/L1-DISPOSABLE"
cp "/workspace/shared/downloads/Havenline/camp16/Source/Fixtures/$fixture.json" "$p/field-inventory-v1.json"
for mode in "$@"; do
  XDG_DATA_HOME="$out/data" XDG_CONFIG_HOME="$out/config" XDG_CACHE_HOME=/tmp/havenline-t01-closure/cache LP_NUM_THREADS=1 timeout 130 godot --headless --path "$project" --audio-driver Dummy --fixed-fps 60 --script res://tests/qa_personal_goods.gd -- "--l1-disposable-profile=$p" "--personal-goods=$mode" > "$out/$mode.log" 2>&1 || printf '%s failed\n' "$mode"
done
