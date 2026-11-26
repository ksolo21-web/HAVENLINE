from pathlib import Path
import hashlib,json,math,sys,struct
import numpy as np
from scipy.spatial.transform import Rotation as Rot
import stock as S
h=Path(__file__).resolve().parent
proj=S.p.parents[2]
scene=(proj/'previews/integrated_opening.gd').read_text()
assert 'minf(4.0 * dt, 4.0 / 30.0)' in scene and 'Vector2(-3.25, 5.80)' in scene
assert 'camera.size = 13.0' in scene and 'Vector3(7, 11, 11)' in scene
assert 'hero_locomotion.observe(here.distance_to(observed) / dt, actor.is_on_floor())' in scene
assert 'direction = ((touch_now - touch_origin) / 82.0).limit_length()' in scene
assert (proj/'previews/hero_locomotion.gd').read_text().find('RUN_EXIT := 2.65')!=-1
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S.p)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
assert len(S.jp)==66
# Reuse only the previously verified source terrain function (not a 52-rig,
# anatomical input, pilot clip or pose).
from functools import lru_cache
analysis=Path(sys.argv[2])
prefix=(analysis/'source_inputs.py').read_text().split('def sources():')[0].split('def clamp(')[1]
exec('def clamp('+prefix, globals())
for check in ['terrain_source.gd','accepted_t02_surface.gd']:
 control=dict((n,hh) for hh,n in (l.split() for l in (analysis/'SOURCE-SHA256SUMS').read_text().splitlines()))
 assert sha(proj/check)==control[check]
# Exact fit in opening.gd. Actor travels unbounded +Z away from camp on dry
# counterpart of original spawn; it never teleports or changes root scale.
V=S.v; Hsrc=float(V.max(0)[1]-V.min(0)[1]);scale=1.75/Hsrc
offset=np.array([-(V.max(0)[0]+V.min(0)[0])*.5,-V.min(0)[1],-(V.max(0)[2]+V.min(0)[2])*.5]) - S.T[42]
G0=S.evaluate(S.T,S.Q); vp=S.skin(S.T,S.Q)
speed=1.50;duration=.6;sto=.55
world0=np.array([-3.25,0.,11.8])
walkstep=.225
foot_ids={'left':(7,4,1,0),'right':(15,14,11,10)}
sm=lambda a,b,x: np.clip((x-a)/(b-a),0,1)**2*(3-2*np.clip((x-a)/(b-a),0,1))
unit=lambda v:v/np.linalg.norm(v)
def rot(p,q):
 p,q=unit(p),unit(q);r=np.cross(p,q);angle=np.arctan2(np.linalg.norm(r),p@q)
 return Rot.from_rotvec(unit(r)*angle).as_matrix() if np.linalg.norm(r)>1e-13 else np.eye(3)
def point(pr): return np.array([pr[0],ground(pr[0],pr[2]),pr[2]])
def assign_q(t,q,ss,i,g,R):
 q[i]=Rot.from_matrix(np.linalg.inv(g[S.P[i],:3,:3])@R).as_quat()
def w(x):
 return (S.W*(S.J==S.jp.index(x))).sum(axis=1)
feet={}
for name,(th,cal,fo,to) in foot_ids.items():
 wf,wt=w(fo),w(to)
 heel=np.flatnonzero((wf>.999999)&(V[:,2]<-.04)&(V[:,1]<.008))
 ball=np.flatnonzero((wt>.999999)&(V[:,2]>.079)&(V[:,1]<.008))
 ar=[]
 for t in (heel,ball):
  assert len(t)>8
  # A real low, near-medial-position raw source row, not an invented pivot.
  d=vp[t,:]; score=18*d[:,1]+.4*abs(d[:,0]-np.median(d[:,0]))+.22*abs(d[:,2]-np.median(d[:,2]))
  ar.append(int(t[np.argmin(score)]))
 shoes=np.flatnonzero((wf+wt>.80)&(V[:,1]<.13))
 feet[name]=dict(heel=ar[0],ball=ar[1],rows=shoes,heel_rows=heel,ball_rows=ball)
def motion(ph):
 # Continuous authored contact phasing. Upper arms keep one full period of
 # exact embedded WALK rotations/translations (2 periods in the source);
 # legs and HIP are replaced, never stock retimed and passed off as new.
 p=ph%1
 t,q,ss,_=S.anim('preset:biped:walk',p*.5)
 t[40]=S.T[40];q[40]=S.Q[40]
 for nodes in foot_ids.values():
  for a in nodes:t[a]=S.T[a];q[a]=S.Q[a]
 g=S.evaluate(t,q,ss)
 hip=G0[39,:3,3]+np.array([.018*math.cos(2*math.pi*(p-.25)), -.041+.005*math.cos(4*math.pi*(p-.20)),0.])
 t[39]=g[40,:3,:3].T@(hip-g[40,:3,3])
 g=S.evaluate(t,q,ss)
 actor=world0+np.array([0.,0.,speed*duration*ph])
 actor=point(actor)
 req={}
 for name,(th,cal,fo,to) in foot_ids.items():
  fp=0. if name=='left' else .5
  alpha=(ph-fp)%1
  # Determine absolute foothold origin for this limb, not an actor-local pin.
  cycle=math.floor(ph-fp+1e-9)+fp
  step=world0+np.array([0.,0.,cycle*speed*duration+walkstep])
  if alpha<=sto+1e-8:
   launch=-14.5*(1-sm(0,.14,alpha))
   roll=24*sm(.36,sto,alpha)
   ang=launch+roll
   lift=0
   toe_angle=ang if ang<0 else ang*(1-sm(.36,.43,alpha))
  else:
   qphase=(alpha-sto)/(1-sto)
   ang=24-(24+14.5)*sm(0.,1.,qphase)
   step[2]+=speed*duration*sm(0.,1.,qphase)
   lift=.063*math.sin(math.pi*qphase)**1.3
   toe_angle=ang*(sm(0,.25,qphase))
  Rf=Rot.from_euler('x',ang,degrees=True).as_matrix()@G0[fo,:3,:3]
  Rt=Rot.from_euler('x',toe_angle,degrees=True).as_matrix()@G0[to,:3,:3]
  isheel=alpha<.36
  to_heel=1. if isheel else (0. if alpha<=sto+1e-8 else sm(.53,.92,qphase))
  heelrow,ballrow=feet[name]['heel'],feet[name]['ball']
  row=heelrow if isheel else ballrow
  want=point(step+((vp[heelrow]*to_heel+vp[ballrow]*(1-to_heel))+offset)*scale);want[1]+=lift
  Ph=Rf@((S.I[S.jp.index(fo)]@np.r_[S.v[heelrow],1.])[:3])
  Pb=Rf@S.T[to]+Rt@((S.I[S.jp.index(to)]@np.r_[S.v[ballrow],1.])[:3])
  P=Ph*to_heel+Pb*(1-to_heel)
  ankle=(want-actor)/scale-offset-P
  # Two-segment exact-length IK with a forward pole (no inward knee buckle).
  # Preserve thigh/shin twist orientation relative to the original bind axes.
  hip_p=g[th,:3,3]
  a,b=np.linalg.norm(S.T[cal]),np.linalg.norm(S.T[fo])
  span=np.linalg.norm(ankle-hip_p)
  if span>a+b-1e-6: raise RuntimeError((name,ph,alpha,span,a+b))
  direction=(ankle-hip_p)/span
  pole=np.array([(.015 if name=='left' else -.015),0,1.])
  ort=unit(pole-direction*(direction@pole))
  add=(a*a+span*span-b*b)/(2*span)
  knee=hip_p+direction*add+ort*math.sqrt(a*a-add*add)
  Rt0=rot(G0[cal,:3,3]-G0[th,:3,3],knee-hip_p)@G0[th,:3,:3]
  Rc0=rot(G0[fo,:3,3]-G0[cal,:3,3],ankle-knee)@G0[cal,:3,:3]
  gy=S.evaluate(t,q,ss)
  assign_q(t,q,ss,th,gy,Rt0)
  gy=S.evaluate(t,q,ss)
  assign_q(t,q,ss,cal,gy,Rc0)
  gy=S.evaluate(t,q,ss)
  assign_q(t,q,ss,fo,gy,Rf)
  gy=S.evaluate(t,q,ss)
  assign_q(t,q,ss,to,gy,Rt)
  gy=S.evaluate(t,q,ss)
  assert np.linalg.norm(gy[fo,:3,3]-ankle)<2e-6
  bend=math.degrees(math.acos(np.clip(unit(knee-hip_p)@unit(ankle-knee),-1,1)))
  req[name]=dict(row=row,type=('heel' if isheel else 'ball'),alpha=alpha,foot_pitch_deg=ang,ball_pitch_deg=toe_angle,
                 target=want,plant=alpha<=sto+1e-8,bend_deg=bend,knee_forward_offset_m=float((knee-(hip_p+direction*add))[2]*scale),ankle=ankle)
 return t,q,ss,req,actor

def ground_batch(a):
 g=np.floor(a[:,[0,2]]*4).astype(int)
 c,inv=np.unique(g,axis=0,return_inverse=True)
 b=np.asarray([[vertex(i*.25,j*.25)[0],vertex((i+1)*.25,j*.25)[0],vertex(i*.25,(j+1)*.25)[0],vertex((i+1)*.25,(j+1)*.25)[0]] for i,j in c])
 dx,dz=(a[:,[0,2]]*4-g).T
 A,B,C,D=b[inv].T
 return np.where(dx+dz<=1,A+(B-A)*dx+(C-A)*dz,D+(B-D)*(1-dz)+(C-D)*(1-dx))
if __name__=='__main__':
 layouts=[];raw=[]
 planar=[]
 yaw=unit(np.cross([0,1,0],[7,11,11])); view=unit(np.array([7,11,11])); up=np.cross(view,yaw)
 mtx=np.c_[yaw,up]*720/13
 for k in range(73):
  f=k/72
  t,q,s,r,a=motion(f)
  # Exact skinned surface rows, not idealized pucks replacing the boots.
  rt=(S.skin(t,q,s)+offset)*scale+a
  ot,oq,os,end=S.anim('preset:biped:walk',f*duration/2.3333332538604736)
  orig=(S.skin(ot,oq,os)+offset)*scale+a
  capture={}
  for name,re in r.items():
   rows=feet[name]['rows'];e=rt[rows,1]-ground_batch(rt[rows])
   base=orig[rows,1]-ground_batch(orig[rows])
   row=re['row'];err=rt[row]-re['target']
   capture[name]=dict(phase=float(re['alpha']),classification=re['type'],plant=re['plant'],support_row=row,
                     actual_sole_min_mm=float(e.min()*1000),stock_sole_min_mm=float(base.min()*1000),
                     exact_anchor_err_mm=float(np.linalg.norm(err)*1000) if re['plant'] else None,
                     actual_stable_rows_within_2mm=int(sum((e>=-.001)&(e<=.002))),
                     knee_flex_deg=re['bend_deg'],knee_forward_offset_mm=re['knee_forward_offset_m']*1000,
                     foot_pitch_deg=float(re['foot_pitch_deg']),ball_pitch_deg=float(re['ball_pitch_deg']),
                     **{'heel_ball_delta_deg':float(re['foot_pitch_deg']-re['ball_pitch_deg'])},
                     marker_world_m=rt[row].tolist(),anchor_target_m=re['target'].tolist())
  raw.append((t,q,s)); layouts.append(dict(seconds=round(duration*f,8),actor_authored_world_m=a.tolist(),feet=capture))
  planar.append(np.stack((np.min((rt-a)@mtx,axis=0),np.max((rt-a)@mtx,axis=0))).tolist())
 D=S.d; binary=bytearray(S.raw);js=lambda k:json.dumps(k,separators=(',',':')).encode('utf-8')
 origmesh=js(D['meshes']);orignodes=js(D['nodes']);origskin=js(D['skins'])
 origtracks=js(D['animations'])
 add=[]
 def channel(vals,node,path):
  nvec=vals.shape[1]
  vv=vals.astype('<f4').tobytes()
  if len(binary)%4:binary.extend(b'\0'*(-len(binary)%4))
  j=len(D['bufferViews'])
  D['bufferViews'].append(dict(buffer=0,byteOffset=len(binary),byteLength=len(vv)))
  binary.extend(vv)
  i=len(D['accessors'])
  acc=dict(bufferView=j,componentType=5126,count=len(vals),type=('SCALAR' if nvec==1 else 'VEC'+str(nvec)))
  if nvec==1:acc.update(min=[float(vals.min())],max=[float(vals.max())])
  D['accessors'].append(acc);return i
 tm=np.linspace(0,duration,len(raw))[:,None]
 time=channel(tm,0,'time')
 B=np.stack([b[0] for b in raw]);C=np.stack([b[1] for b in raw]);E=np.stack([b[2] for b in raw])
 channels=[];samplers=[]
 for i in S.jp:
  for tag,values in [('translation',B[:,i]),('rotation',C[:,i]),('scale',E[:,i])]:
   if i==40 or not np.any(np.abs(values-{'translation':S.T,'rotation':S.Q,'scale':S.S}[tag][i])>1e-8):continue
   if tag=='rotation':
    for j in range(1,len(values)):
     if values[j]@values[j-1]<0:values[j]*=-1
   channels.append(dict(sampler=len(samplers),target=dict(node=i,path=tag)))
   samplers.append(dict(input=time,output=channel(values,i,tag),interpolation='LINEAR'))
 D['animations'].append(dict(name='Havenline_stock66_contact_walk_take_v1',samplers=samplers,channels=channels))
 assert js(D['meshes'])==origmesh and js(D['nodes'])==orignodes and js(D['skins'])==origskin and js(D['animations'][:-1])==origtracks
 assert binary[:len(S.raw)]==S.raw
 D['buffers'][0]['byteLength']=len(binary)
 j=bytearray(js(D));j.extend(b' '*(-len(j)%4));binary.extend(b'\x00'*(-len(binary)%4))
 out=struct.pack('<4sII',b'glTF',2,12+16+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\x00')+binary
 dst=h/'Character1-Stock66ContactWalk.LOCAL.glb';dst.write_bytes(out)
 for role in ('left','right'):
  arr=[a['feet'][role] for a in layouts]
  planted=[e for e in arr if e['plant']]
  print(role,'anchor mm',max(t['exact_anchor_err_mm'] for t in planted),'lowest mm',min(t['actual_sole_min_mm'] for t in arr),'unsupported stable frames',sum(t['actual_stable_rows_within_2mm']==0 for t in planted),'stock min',min(t['stock_sole_min_mm'] for t in arr),'min knee fwd',min(t['knee_forward_offset_mm'] for t in arr))
 result={'scope':'single 0.6 s detached dry-snow comparison take; not periodic runtime integration','source_sha256':sha(S.p),'unchanged_original_binary_prefix_bytes':len(S.raw),'candidate_sha256':sha(dst),'joint_count':len(S.jp),'clip_channels':len(channels),'source_camera_max_projected_extents_xy_px':np.max(planar,axis=0).tolist(),'walk_input_speed_m_s':speed,'touch_offset_px':82*speed/4,'start_scene_xz_m':world0[[0,2]].tolist(),'model_fit_scale':scale,'source_file_sha256':{str(x.relative_to(proj)):sha(x) for x in [proj/'layout.json',proj/'opening.gd',proj/'previews'/'integrated_opening.gd',proj/'previews'/'hero_locomotion.gd',proj/'terrain_source.gd',proj/'accepted_t02_surface.gd'] if x.is_file()},'frames':layouts}
 (h/'measurements.json').write_text(json.dumps(result,indent=2)+'\n')
