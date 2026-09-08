shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_disabled;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float surface_roughness = 0.95;
instance uniform float cutaway : instance_index(0) = 0.0;
void fragment() {
 // Opaque stochastic cutaway works on Mobile; GeometryInstance3D.transparency does not.
 float coverage = fract(52.9829189 * fract(dot(FRAGCOORD.xy,vec2(0.06711056,0.00583715))));
 if (coverage < cutaway) { discard; }
 ALBEDO=texture(albedo_texture,UV).rgb * COLOR.rgb;
 NORMAL_MAP=texture(normal_texture,UV).rgb;
 NORMAL_MAP_DEPTH=.38;
 ROUGHNESS=surface_roughness;
 SPECULAR=.18;
}
