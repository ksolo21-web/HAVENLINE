set -eu
area=/tmp/havenline-t05-wide
project="$1"
mode="$2"
file="$3"
out="$area/$mode"
profile=$(mktemp -d /tmp/havenline-l1-v3-t05wide-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
if test "$#" -ge 4; then
  cp "/workspace/shared/downloads/Havenline/camp16/Source/Fixtures/$4.json" "$profile/field-inventory-v1.json"
fi
cache="$out/data/Havenline-Level-1-Settlement-Trial"
mkdir -p "$cache"
ln -sf /tmp/havenline-t01-closure/shader-cache "$cache/shader_cache"
export HAVENLINE_WIDE_EVIDENCE="$out" HAVENLINE_PATCH_EVIDENCE="$out" OWL_EVIDENCE_JSON="$out/Patrol.json" DISPLAY=:129 LP_NUM_THREADS=2 LIBGL_ALWAYS_SOFTWARE=1 MESA_SHADER_CACHE_DISABLE=true
export XDG_DATA_HOME="$out/data" XDG_CONFIG_HOME="$out/config" XDG_CACHE_HOME=/tmp/havenline-t01-closure/cache
sha256sum "$project"/field_{owl,carry,art,opening,goods_pack,goods_exchange}.gd "$project/assets/settlement_people/expedition_plumage.gdshader" > "$out/Source.sha256"
flock /tmp/hl13/render.lock timeout 175 godot --path "$project" --rendering-method gl_compatibility --windowed --resolution 960x540 --disable-render-loop --audio-driver Dummy --fixed-fps 60 --script "$file" -- "--l1-disposable-profile=$profile" > "$out/Native.log" 2>&1
