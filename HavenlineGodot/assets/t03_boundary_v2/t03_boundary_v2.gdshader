shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color=vec4(1.0);
uniform float roughness_value=0.85;
uniform float metallic_value=0.0;
uniform vec3 emission_color=vec3(0.0);
uniform float detail_strength=0.05;
uniform float detail_scale=3.0;
varying vec3 world_position;
float h(vec3 q){q=fract(q*.1031);q+=dot(q,q.yzx+33.33);return fract((q.x+q.y)*q.z);}
void vertex(){world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;}
void fragment(){float g=(h(floor(world_position*detail_scale))-.5)*2.;ALBEDO=clamp(base_color.rgb*(1.+g*detail_strength),vec3(0.),vec3(1.));ROUGHNESS=roughness_value;METALLIC=metallic_value;EMISSION=emission_color;}
