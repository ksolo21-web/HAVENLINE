shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_back;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float surface_roughness = 0.95;
instance uniform float cutaway : instance_index(0) = 0.0;
uniform bool player_clearance_enabled = false;
uniform vec3 player_focus_world = vec3(0.0);
varying float forest_clearance;
void vertex() {
 // MODEL_MATRIX includes the individual MultiMesh transform. This makes the
 // player sightline work for every tree, without fading an entire forest cell.
 forest_clearance = 0.0;
 if (player_clearance_enabled) {
  vec3 base = (VIEW_MATRIX * vec4(MODEL_MATRIX[3].xyz,1.0)).xyz;
  vec3 top = (VIEW_MATRIX * MODEL_MATRIX * vec4(0.0,3.6,0.0,1.0)).xyz;
  vec3 focus = (VIEW_MATRIX * vec4(player_focus_world,1.0)).xyz;
  float scale_x = length(MODEL_MATRIX[0].xyz);
  float across = 1.0-smoothstep(0.45*scale_x,1.55*scale_x,abs(focus.x-base.x));
  float below = smoothstep(min(base.y,top.y)-0.20,min(base.y,top.y)+0.42,focus.y);
  float above = 1.0-smoothstep(max(base.y,top.y)-0.05,max(base.y,top.y)+0.35,focus.y);
  float in_front = smoothstep(0.15,1.10,max(base.z,top.z)-focus.z);
  forest_clearance = across*below*above*in_front;
 }
}
void fragment() {
 // Opaque dither, not Mobile-unsupported instance transparency. No blend-order
 // changes, gameplay deletion, material replacement or whole-batch hiding.
 float coverage = fract(52.9829189*fract(dot(FRAGCOORD.xy,vec2(0.06711056,0.00583715))));
 if (coverage < max(cutaway,forest_clearance)) { discard; }
 ALBEDO = texture(albedo_texture,UV).rgb*COLOR.rgb;
 // Restrained cool silhouette shading preserves the reference crown separation.
 ALBEDO *= mix(0.64,1.0,smoothstep(0.0,0.18,abs(dot(NORMAL,VIEW))));
 NORMAL_MAP = texture(normal_texture,UV).rgb;
 NORMAL_MAP_DEPTH = 0.38;
 ROUGHNESS = surface_roughness;
 SPECULAR = 0.18;
}
