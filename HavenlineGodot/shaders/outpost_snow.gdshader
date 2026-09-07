shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec2 furnace_center = vec2(0.0,0.2);
uniform float warmth_radius = 4.5;
uniform float heat_strength = 1.0;
uniform float snow_amount = 0.03;
varying vec3 world_pos;
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p) {
 vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
 return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
}
float path_distance(vec2 p, vec2 a, vec2 b) {
 vec2 v=b-a; return length(p-a-v*clamp(dot(p-a,v)/dot(v,v),0.0,1.0));
}
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 p=world_pos.xz; float n=noise(p*1.2); float grain=noise(p*21.0);
 float dist=length(p-furnace_center);
 float warm=(1.0-smoothstep(warmth_radius-0.80,warmth_radius+0.10,dist))*heat_strength;
 float melt=(1.0-smoothstep(warmth_radius-1.8,warmth_radius-0.1,dist+(n-.5)*.6))*heat_strength;
 float path=min(path_distance(p,vec2(0,6.2),furnace_center),path_distance(p,vec2(-2.8,2.25),furnace_center));
 float compact=(1.0-smoothstep(.35,1.05,path))*(1.0-snow_amount*.32);
 vec3 snow=mix(vec3(.69,.82,.91),vec3(.93,.97,1.0),.38+n*.45+grain*.12);
 snow=mix(snow,vec3(.60,.72,.79),compact*.28);
 vec3 ground=mix(vec3(.23,.28,.29),vec3(.38,.36,.31),noise(p*3.4));
 ground=mix(ground,vec3(.50,.50,.46),smoothstep(.84,.96,grain)*.22);
 ALBEDO=mix(pow(snow,vec3(2.2)),pow(ground,vec3(2.2)),melt*.88);
 ROUGHNESS=mix(.89,.73,melt);
 SPECULAR=.23;
 EMISSION=vec3(.08,.032,.006)*warm*(1.0-smoothstep(0.,warmth_radius,dist));
}
