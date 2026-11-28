set -eu
project=$1
out=$2
spec=$3
fixture=$4
mkdir -p "$out"
profile=$(mktemp -d /tmp/havenline-l1-v3-wide-receiver-XXXXXXXX)
printf 'HAVENLINE-ALFRED-V3-DISPOSABLE\n' > "$profile/L1-DISPOSABLE"
cp "/workspace/shared/downloads/Havenline/camp16/Source/Fixtures/$fixture.json" "$profile/field-inventory-v1.json"
mkdir -p "$out/data/Havenline-Level-1-Settlement-Trial"
ln -sf /tmp/havenline-t01-closure/shader-cache "$out/data/Havenline-Level-1-Settlement-Trial/shader_cache"
export XDG_DATA_HOME="$out/data" XDG_CONFIG_HOME="$out/config" XDG_CACHE_HOME=/tmp/havenline-t01-closure/cache DISPLAY=:129 LP_NUM_THREADS=2 LIBGL_ALWAYS_SOFTWARE=1 MESA_SHADER_CACHE_DISABLE=true
export HAVENLINE_PATCH_EVIDENCE="$out"
export HL_RECEIVING_SEED="$fixture"
for f in field_conveyor_{network,gauge,receiver,receiver_art,fittings,aisles}.gd field_conveyors.gd field_counter.gd field_settlement_loop.gd assets/conveyors/fitted_transport.gdshader; do if test -f "$project/$f"; then sha256sum "$project/$f"; fi; done > "$out/Source.sha256"
flock /tmp/hl13/render.lock timeout 200 godot --path "$project" --rendering-method gl_compatibility --resolution 960x540 --disable-render-loop --audio-driver Dummy --fixed-fps 60 --script "$spec" -- "--l1-disposable-profile=$profile" > "$out/Native.log" 2>&1
