shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
// COLOR.r = T02 river shore distance, COLOR.g = warm workfloor distance,
// COLOR.b = T03 packed-lane signed distance. All three are CPU-authored from
// gameplay geometry so visible paths cannot diverge from route checks.
uniform vec2 furnace_center = vec2(0.0,0.2);
uniform float warmth_radius = 4.5;
uniform float heat_strength = 1.0;
uniform float snow_amount = 0.03;
uniform float daylight_fill = 1.0;
varying vec3 world_pos;
varying vec3 authored_distance;
float material_hash(vec2 p){
 vec3 h=fract(vec3(p.xyx)*vec3(.1031,.1030,.0973));
 h+=dot(h,h.yzx+33.33);return fract((h.x+h.y)*h.z);
}
float material_noise(vec2 p){
 vec2 cell=floor(p), f=fract(p);f=f*f*(3.-2.*f);
 return mix(mix(material_hash(cell),material_hash(cell+vec2(1,0)),f.x),
            mix(material_hash(cell+vec2(0,1)),material_hash(cell+vec2(1,1)),f.x),f.y);
}
void vertex(){
 world_pos=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;
 authored_distance=COLOR.rgb*8.-4.;
}
void fragment(){
 vec2 p=world_pos.xz;
 float shore=authored_distance.x;
 float d=authored_distance.y;
 float lane=authored_distance.z;
 float broad=material_noise(p*.37)-.5;
 float fine=material_noise(p*7.8)-.5;
 float footprint=max(length(dFdx(p)),length(dFdy(p)));
 float detail_weight=1.-smoothstep(.025,.16,footprint);
 vec3 snow=vec3(.98,.994,1.0)+vec3(.042,.029,.016)*broad;
 snow+=vec3(.012,.010,.008)*fine*detail_weight;
 float rim=(1.-smoothstep(.04,.48,d))*smoothstep(-.16,.04,d);
 snow=mix(snow,vec3(.73,.82,.94),rim*.16);
 float aa=max(fwidth(d)*.75,.022);
 float edge_d=d+(material_noise(p*1.6)-.5)*.035;
 float cleared=1.-smoothstep(-.08-aa,.13+aa,edge_d);
 vec3 floor=vec3(.80,.48,.36)+vec3(.09,.058,.043)*broad;
 floor+=vec3(.022,.015,.011)*fine*detail_weight;
 float dist=length(p-furnace_center);
 float warmth=(1.-smoothstep(warmth_radius-.4,warmth_radius+.12,dist))*heat_strength;
 floor=mix(floor,floor+vec3(.025,.012,0.),warmth*.42);
 vec3 material=mix(snow,floor,cleared);

 // T03 lanes remain compressed/worn material in the SAME terrain surface.
 // Source-bound gate preflight showed that the prior blue-grey compression was
 // still too close to untouched snow at river approaches. Increase value and
 // temperature separation enough to read without captions, while preserving
 // broad/fine variation and a noisy edge so it never becomes a painted stripe.
 float lane_noise=(material_noise(p*1.17)-.5)*.115+(material_noise(p*3.35)-.5)*.055;
 float lane_aa=max(fwidth(lane)*.8,.025);
 float lane_edge_d=lane+lane_noise;
 float lane_mask=1.-smoothstep(-.07-lane_aa,.18+lane_aa,lane_edge_d);
 // Full-range macro compression survives gameplay/contact-sheet reduction;
 // the prior mid-frequency-only term disappeared at river evidence scale.
 // Both terms remain inside the authored route SDF on the terrain itself.
 float packed_macro=material_noise(p*.68+vec2(4.7,-2.1));
 float packed_mid=material_noise(p*2.15+vec2(-1.3,3.8));
 float packed_compression=smoothstep(.12,.86,packed_macro*.68+packed_mid*.32);
 // Keep the compressed bed recognisably snowy, then cut paired irregular
 // traffic ruts through it. This replaces the former broad grey overlay read
 // with visible compression marks on the continuous authored terrain.
 vec3 packed_snow=mix(vec3(.60,.64,.64),vec3(.84,.85,.82),packed_compression);
 packed_snow+=vec3(.030,.028,.025)*fine*detail_weight;
 float packed_scuff=smoothstep(.50,.78,material_noise(p*3.35+vec2(2.2,5.1)));
 float packed_clump=smoothstep(.43,.72,material_noise(p*1.28+vec2(-5.4,1.7)));
 packed_snow*=1.-packed_scuff*.10;
 packed_snow=mix(packed_snow,vec3(.48,.43,.36),packed_clump*.20);
 packed_snow+=vec3(.060,.041,.024)*(packed_mid-.5);
 float packed_core=1.-smoothstep(-.76,-.24,lane_edge_d);
 float lane_center_distance=max(lane+1.30,0.0);
 float paired_rut=1.-smoothstep(.09,.28,abs(lane_center_distance-.62));
 float rut_breakup=.84+.16*smoothstep(.22,.76,material_noise(p*2.72+vec2(7.1,-4.3)));
 packed_snow=mix(packed_snow,vec3(.20,.17,.13),paired_rut*lane_mask*rut_breakup*.94);
 float churned_snow=smoothstep(.68,.88,material_noise(p*1.92+vec2(-8.4,2.6)));
 packed_snow=mix(packed_snow,vec3(.78,.80,.77),churned_snow*lane_mask*.30);
 packed_snow*=1.-packed_core*(.055+packed_mid*.025);
 // Warm-ground wear stays clearly related to the existing camp floor, but is
 // compressed/duller so the same route can be followed across the snow/floor join.
 vec3 packed_floor=mix(floor*.74+vec3(.040,.024,.016),floor*.90+vec3(.018,.011,.007),packed_compression);
 packed_floor*=1.-packed_scuff*.08;
 packed_floor=mix(packed_floor,packed_floor*vec3(.90,.86,.80),packed_clump*.18);
 packed_floor+=vec3(.042,.027,.016)*(packed_mid-.5);
 packed_floor=mix(packed_floor,vec3(.19,.105,.065),paired_rut*lane_mask*rut_breakup*.90);
 packed_floor*=1.-packed_core*(.045+packed_mid*.022);
 vec3 packed=mix(packed_snow,packed_floor,cleared);
 float wear=clamp(.84+material_noise(p*2.05)*.12+material_noise(p*5.1)*.06,.82,1.0);
 material=mix(material,packed,lane_mask*.97*wear);
 float lane_edge=(1.-smoothstep(.08,.38,abs(lane_edge_d)))*smoothstep(-.10,.018,abs(lane_edge_d));
 material=mix(material,material*.87,lane_edge*.48);

 float ice=1.-smoothstep(-.12,.035,shore);
 material=mix(material,vec3(.37,.67,.84),ice*.35);
 ALBEDO=pow(clamp(material,vec3(0.),vec3(1.)),vec3(2.2));
 EMISSION=vec3(.030,.034,.040)*(1.-cleared)*clamp(daylight_fill,0.,1.);
 float sx=cos(p.x*8.1+p.y*3.7)*.006;
 float sz=cos(p.x*-4.6+p.y*9.3)*.006;
 NORMAL=normalize(NORMAL+(VIEW_MATRIX*vec4(-sx,0.,-sz,0.)).xyz*detail_weight);
 ROUGHNESS=clamp(mix(.92,.88,cleared)+fine*.028*detail_weight+lane_mask*.018,.84,.96);
 SPECULAR=.18;
}
