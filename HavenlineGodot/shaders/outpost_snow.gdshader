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
float boot_track(vec2 p, vec2 a, vec2 b) {
 vec2 dir=normalize(b-a); vec2 side=vec2(-dir.y,dir.x);vec2 d=p-a;
 float along=dot(d,dir);float lane=dot(d,side);
 float stride=floor(along/.58);float phase=fract(along/.58)-.5;
 float lateral=lane-(mod(stride,2.0)*2.0-1.0)*.16;
 float oval=length(vec2(phase*.58/.14,lateral/.072));
 return (1.0-smoothstep(.76,1.16,oval))*step(0.0,along)*step(along,length(b-a));
}
void vertex() { world_pos = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 p=world_pos.xz;
 float broad=noise(p*.58);float n=noise(p*2.7);float grain=noise(p*29.0);
 float dist=length(p-furnace_center);
 float warm=(1.0-smoothstep(warmth_radius-.80,warmth_radius+.10,dist))*heat_strength;
 float melt=(1.0-smoothstep(warmth_radius-1.50,warmth_radius+.05,dist+(broad-.5)*.72))*heat_strength;
 float path=min(path_distance(p,vec2(0,12.2),furnace_center),path_distance(p,vec2(-2.8,2.25),furnace_center));
 path=min(path,path_distance(p,vec2(-6.6,-3.65),furnace_center));
 path=min(path,path_distance(p,vec2(6.6,-3.65),furnace_center));
 path=min(path,path_distance(p,vec2(0,-10.7),furnace_center));
 float compact=(1.0-smoothstep(.32,1.02,path+(broad-.5)*.29))*(1.0-snow_amount*.44);
 float ripple=sin(p.x*3.8+p.y*1.35+broad*3.0)*.5+.5;
 vec3 snow=mix(vec3(.72,.84,.91),vec3(.92,.96,.98),.38+broad*.32+n*.15+grain*.08);
 snow=mix(snow,vec3(.58,.73,.82),compact*.49);
 float prints=max(boot_track(p,furnace_center,vec2(-6.6,-3.65)),boot_track(p,furnace_center,vec2(6.6,-3.65)));
 prints=max(prints,boot_track(p,vec2(0,12.2),furnace_center))*(1.0-snow_amount*.85);
 snow=mix(snow,vec3(.45,.59,.68),prints*.29);
 snow*=.973+.027*ripple;
 vec3 ground=mix(vec3(.29,.32,.32),vec3(.47,.43,.35),n*.58+broad*.35);
 float stones=smoothstep(.82,.93,noise(p*13.0));
 ground=mix(ground,vec3(.56,.56,.50),stones*.36);
 ground=mix(ground,vec3(.19,.23,.26),(1.0-smoothstep(.8,2.0,dist))*heat_strength*.55);
 ALBEDO=mix(pow(snow,vec3(2.2)),pow(ground,vec3(2.2)),melt*.93);
 ROUGHNESS=mix(.88,.79,melt)-stones*melt*.06;
 SPECULAR=.25;
 float dx=noise((p+vec2(.017,0))*29.0)-grain;
 float dz=noise((p+vec2(0,.017))*29.0)-grain;
 NORMAL_MAP=normalize(vec3(-dx*.24,-dz*.24,1.0))*.5+.5;
 NORMAL_MAP_DEPTH=.6;
 EMISSION=vec3(.03,.012,.002)*warm*(1.0-smoothstep(0.,warmth_radius,dist));
}
