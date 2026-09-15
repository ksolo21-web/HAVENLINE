shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_back, shadows_disabled;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float surface_roughness = 0.95;
instance uniform float cutaway : instance_index(0) = 0.0;
uniform bool player_clearance_enabled = false;
uniform vec3 player_focus_world = vec3(0.0);
varying float forest_clearance;
void vertex() {
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
 float coverage = fract(52.9829189*fract(dot(FRAGCOORD.xy,vec2(0.06711056,0.00583715))));
 if (coverage < max(cutaway,forest_clearance)) { discard; }
 vec3 surface_color = texture(albedo_texture,UV).rgb;
 float wood = step(surface_color.b*1.25,surface_color.r);
 // Tree-only stylized palette calibration in linear light. It compensates
 // the existing scene's warm/gray response, not the screen or world lighting.
 // Both the original video samples and the prior actual render were measured.
 float band = clamp(floor(UV.y*3.0),0.0,2.0)*0.5;
 vec3 snow_gain = mix(vec3(0.40,0.74,1.42),vec3(0.50,0.90,1.40),band);
 vec3 wood_gain = vec3(0.22,0.30,0.48);
 ALBEDO = surface_color*mix(COLOR.rgb,vec3(1.0),wood)*mix(snow_gain,wood_gain,wood);
 ALBEDO *= mix(mix(0.10,0.65,wood),1.0,smoothstep(0.04,0.22,abs(dot(NORMAL,VIEW))));
 NORMAL_MAP = texture(normal_texture,UV).rgb;
 NORMAL_MAP_DEPTH = 0.38;
 ROUGHNESS = surface_roughness;
 SPECULAR = 0.18;
 AO = mix(0.88,1.0,wood);
 AO_LIGHT_AFFECT = 0.0;
 // Directional shape lighting and cast ground shadows remain. No emission,
 // unshaded mode, extra render pass, reduced resolution or global color grade.
}
