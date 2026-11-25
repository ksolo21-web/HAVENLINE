import bpy, sys, hashlib, json, numpy as np, math
from pathlib import Path
from mathutils import Quaternion,Vector
p=Path(sys.argv[-1]); sha=hashlib.sha256(p.read_bytes()).hexdigest()
assert sha=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(p))
sc=bpy.context.scene
rig=next(o for o in sc.objects if o.type=='ARMATURE'); m=next(o for o in sc.objects if o.type=='MESH')
ad=rig.animation_data; ad.use_nla=False
for t in ad.nla_tracks:t.mute=True
def vertices(ev):
 ob=m.evaluated_get(bpy.context.evaluated_depsgraph_get()) if ev else m
 me=ob.data
 co=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',co)
 mat=np.array(ob.matrix_world);return co.reshape(-1,3)@mat[:3,:3].T+mat[:3,3]
rest=vertices(False); lo=rest.min(0); hi=rest.max(0); scale=1.75/(hi-lo)[2]; offset=np.array([(hi[0]+lo[0])/2,(hi[1]+lo[1])/2,lo[2]])
def norm(v):return (v-offset)*scale
rest=norm(rest)
group={vg.index:vg.name for vg in m.vertex_groups}
masks={}
for side in ['L','R']:
 mask=np.array([sum(g.weight for g in v.groups if group[g.group] in (side+'_Foot',side+'_ToeBase'))>.53 for v in m.data.vertices])
 boot=rest[mask]; forward=-1 if np.mean(boot[:,1])<0 else 1
 whole_boot_ids=np.flatnonzero(mask)
 mask &= rest[:,2]<boot[:,2].min()+.03
 fwd=rest[:,1]*forward
 qs=np.quantile(fwd[mask],[.3,.7])
 masks[side]={'heel':mask&(fwd<=qs[0]),'toe':mask&(fwd>=qs[1])}
 assert all(np.sum(x)>10 for x in masks[side].values())
 for patch, pmask in masks[side].items():
  i=np.flatnonzero(pmask)
  masks[side][patch]=i[np.argsort(rest[i,2])[:max(8,len(i)//10)]]
 masks[side]['whole_boot']=whole_boot_ids
print('scale=',scale,'bounds=',lo,hi,'forward=',forward,'counts=',{s:{p:len(x) for p,x in v.items()} for s,v in masks.items()})
def bp(name):return norm(np.array(rig.matrix_world@rig.pose.bones[name].head))
def angle(x,y):return np.rad2deg(np.arccos(np.clip(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)),-1,1)))
# Fixed heading. Author support windows from contiguous backward near-floor
# Fresh analytic cause: fixed measured heel/ball support, distinct periodic natural clearance,
# fixed anterior knee pole, bounded upper boot articulation. No prior action/weights.
from mathutils import Matrix
ad.action=None
scene=bpy.context.scene
scene.render.fps=120
P=Path(__file__).parent
rates=(240,); duty=.60; T=1.; speed=.66
assert forward==-1
update=bpy.context.view_layer.update
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
update()
worldrot=rig.matrix_world.to_quaternion()
inv=rig.matrix_world.inverted()
localaxis=worldrot.inverted()@Vector((1,0,0))
B={b.name:b.matrix.copy() for b in rig.pose.bones}
def rot(a):return Quaternion(localaxis,math.radians(a)).to_matrix().to_4x4()
def set_global(b,M):
 b.matrix=M
 update()
def at(b,M):
 out=M.copy(); out.translation=b.head
 set_global(b,out)
def normpos(v):return norm(np.asarray(rig.matrix_world@v))
def local(v):return inv@Vector(v/scale+offset)
def quint(x):
 x=max(0.,min(1.,x));return x**3*(10+x*(-15+6*x))
mesh=m.data; mesh.calc_loop_triangles()
edge=np.array([tuple(e.vertices) for e in mesh.edges]); edge.sort(axis=1)
W={}
for v in mesh.vertices:
 for g in v.groups:
  name=group[g.group]
  if name not in W:W[name]=np.zeros(len(mesh.vertices))
  W[name][v.index]=g.weight
leg_edges=[]
restedge=np.linalg.norm(rest[edge[:,0]]-rest[edge[:,1]],axis=1)
for s in ('L','R'):
 mask=W[s+'_Foot']+W[s+'_ToeBase']+W[s+'_Calf']
 sel=(mask[edge].mean(1)>.9)&(restedge>.0008)&(rest[edge,2].mean(1)<.30)
 leg_edges.append(np.flatnonzero(sel))
# Contact anchors: translating heel and toe rest centroids rigidly with virtual body travel.
# Correct only prescribed ankle position to place actual skinned sole centroid; cannot change roll,
# body controls, or weights. No support vertical correction during swing.
rest_patch={s:{p:rest[masks[s][p]].mean(0) for p in ('heel','toe')} for s in ('L','R')}
def leg(s, target, pitch, dig):
 jj=[rig.pose.bones[s+'_'+j] for j in ('Thigh','Calf','Foot','ToeBase')]
 thigh,calf,foot,toe=jj
 a=thigh.head.copy(); b0=B[calf.name].translation; c0=B[foot.name].translation
 t0=B[thigh.name].translation
 L1=(b0-t0).length;L2=(c0-b0).length
 v=local(target)-a; d=v.length; safe=min(d,L1+L2-.006); v.normalize()
 q=worldrot.inverted()@Vector((.11 if normpos(a)[0]>0 else -.11,-1,0))
 q=(q-v*q.dot(v)).normalized()
 k=(L1*L1-L2*L2+safe*safe)/(2*safe)
 b=a+v*k+q*math.sqrt(max(0,L1*L1-k*k))
 c=a+v*safe
 for j,base,end in [(thigh,b0-t0,b-a),(calf,c0-b0,c-b)]:
  at(j,base.rotation_difference(end).to_matrix().to_4x4()@B[j.name])
 at(foot,rot(pitch)@B[foot.name])
 at(toe,rot(pitch+dig)@B[toe.name])
 return float((normpos(foot.head)-target).dot(normpos(foot.head)-target)**.5)
import itertools
tri=np.array([tuple(s.vertices) for s in mesh.loop_triangles])
tris={}
for s in ('L','R'):
 weights=W[s+'_Foot']+W[s+'_ToeBase']; boot=weights>.53
 sole=boot&(rest[:,2]<rest[boot,2].min()+.030)
 f=-rest[:,1]; q=np.quantile(f[sole],[.3,.7])
 for kind,sel in {'heel':sole&(f<=q[0]),'toe':sole&(f>=q[1])}.items():
  ids=tri[sel[tri].all(1)]
  tris[(s,kind)]=ids
ids={s:masks[s]['whole_boot'] for s in ('L','R')}
# Signed physical thresholds. Contact means one welded connected projected surface,
# not scattered isolated near-floor points. Source mesh is unmodified.
from collections import defaultdict
def area_contact(xyz,s,kind):
 t=tris[(s,kind)]; v=xyz[t]
 take=((v[:,:,2]>=-.001)&(v[:,:,2]<=.002)).all(1)
 u=v[take]; tind=t[take]
 if not len(u):return 0.,None,0
 ab=u[:,1,:2]-u[:,0,:2];ac=u[:,2,:2]-u[:,0,:2]
 areas=np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])*.5
 # Weld raw position seams by exact near-rest identity, then connect only by shared edges.
 welded=np.rint(rest[tind]/1e-6).astype('int64')
 links=defaultdict(list); parent=list(range(len(u)))
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 for i,tt in enumerate(welded):
  for a,b in ((0,1),(1,2),(2,0)):
   key=tuple(sorted((tuple(tt[a]),tuple(tt[b]))))
   for j in links[key]:parent[root(i)]=root(j)
   links[key].append(i)
 groups=defaultdict(list)
 for i in range(len(u)):groups[root(i)].append(i)
 win=max(groups.values(),key=lambda i:float(areas[i].sum()))
 a=areas[win].sum()
 return (float(a),np.average(u[win].mean(axis=1)[:,:2],axis=0,weights=areas[win]) if a>1e-12 else None,len(win))
def reset(tick):
 ph=tick/240
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 update()
 p=rig.pose.bones['Hip'];M=B[p.name].copy()
 M.translation=local(normpos(M.translation)+np.array([.014*math.sin(2*math.pi*ph),0.,-.065+.008*(1-math.cos(4*math.pi*(ph-.055)))]))
 set_global(p,M)
def check(s, kind, target, pitch, dig):
 xyz=norm(vertices(True))
 a, xy, nt=area_contact(xyz,s,kind)
 low=float(xyz[ids[s],2].min())
 ix=leg_edges[('L','R').index(s)]
 es=edge[ix]; ratios=np.linalg.norm(xyz[es[:,0]]-xyz[es[:,1]],axis=1)/restedge[ix]
 return {'s':s,'kind':kind,'pitch':pitch,'digit':dig,'target':target.tolist(),'floor_mm':low*1000,'worst_raw_boot_vertex':int(ids[s][xyz[ids[s],2].argmin()]),'area_mm2':a*1e6,'near_triangles':nt,'centroid_xy':None if xy is None else xy.tolist(),'edge_ratio_min':float(ratios.min()),'edge_ratio_max':float(ratios.max()),'edges_lt_half':int((ratios<.5).sum()),'worst_edge':int(ix[ratios.argmin()]),'reach_error_mm':float(np.linalg.norm(normpos(rig.pose.bones[s+'_Foot'].head)-target))*1000}
def passes(c):
 return c['floor_mm']>=-1 and c['area_mm2']>=9 and c['near_triangles']>=2 and c['pinned_patch_xy_error_mm']<=1.0 and c['edge_ratio_min']>=.5 and c['edge_ratio_max']<=2 and c['reach_error_mm']<=.1
# Fresh held static authoring: whole L lower chain rotated from its measured
# original stock anatomical base about the hip, never the rejected IK target.
ph=-4.
ar=rig.pose.bones['L_Thigh']
pel=rig.pose.bones['Hip']
world=-np.array([0.,1.,0.])
old=bpy.context.view_layer
rest_b={k:normpos(B['L_'+k].translation) for k in ('Thigh','Calf','Foot','ToeBase')}
sp=rot(ph)
root0=B[ar.name].translation.copy()
swing=sp@B[ar.name];swing.translation=root0
set_global(ar,swing)
raw0=norm(vertices(True)); idsL=ids['L']
# Geometry-driven floor support. Global pelvis vertical translation (not ankle target)
# so the prescribed shank and all local articulation angles remain exactly unchanged.
needed=.00015-float(raw0[idsL,2].min())
basep=B[pel.name].copy()
v=np.array([0.,0.,needed])
basep.translation=local(normpos(basep.translation)+v)
set_global(pel,basep)
# Expected local armature inheritance remains a pure +z for all rest stock poses.
xyz=norm(vertices(True))
guard=leg_edges[0]; eg=edge[guard]
rr=np.linalg.norm(xyz[eg[:,1]]-xyz[eg[:,0]],axis=1)/restedge[guard]
act={k:normpos(rig.pose.bones['L_'+k].head) for k in rest_b}
a,uv,nt=area_contact(xyz,'L','heel')
at,ut,tt=area_contact(xyz,'L','toe')
knee_rel=act['Calf']-act['Thigh']
ankle_rel=act['Foot']-act['Calf']
base0=rest_b['Calf']-rest_b['Thigh'];base1=rest_b['Foot']-rest_b['Calf']
def direction(v):
 return np.array([math.degrees(math.atan2(-v[1],-v[2])), math.degrees(math.atan2(v[0],-v[2]))])
# Both anatomical segment lengths and knee angle preserved; no engine or rig edit.
basek=angle(-base0,base1); curk=angle(-knee_rel,ankle_rel)
nonL=np.ones(len(rest),dtype=bool)
for nm,w in W.items():
 if nm.startswith('L_') and any(p in nm for p in ('Thigh','Calf','Foot','Toe','Knee','Boot')):
  nonL&=w<1e-8
# Only total pelvis vertical translation is expected beyond the touched leg.
frame_change_error=float(np.linalg.norm((xyz-raw0)-v,axis=1).max())
mask=[s for s in masks['L']['heel']]
r={'asset':sha,'label':'single static left support; right stance neither measured nor asserted','sagittal_tilt_deg':ph,'resulting_pelvis_delta_mm':(v*1000).tolist(),'pelvis_frame_max_error_mm':frame_change_error*1000,'left_bones_rest_m':{k:x.tolist() for k,x in rest_b.items()},'left_bones_posed_m':{k:x.tolist() for k,x in act.items()},'left_shank_direction_forward_lateral_deg':direction(ankle_rel).tolist(),'left_rest_shank_direction_forward_lateral_deg':direction(base1).tolist(),'knee_angle_rest_pose_deg':[basek,curk],'left_ankle_forward_delta_mm':1000*(act['Foot']-rest_b['Foot']).dot(world),'left_actual_sole_low_mm':float(xyz[idsL,2].min())*1000,'left_heel_actual_contact_area_mm2':a*1e6,'left_heel_actual_contact_faces':nt,'left_heel_world_pin_m':None if uv is None else uv.tolist(),'left_toe_area_mm2':at*1e6,'left_toe_low_mm':float(xyz[masks['L']['toe'],2].min())*1000,'left_heel_low_mm':float(xyz[mask,2].min())*1000,'left_edge_ratio':[float(rr.min()),float(rr.max())],'left_bad_edges':int(sum((rr<.5)|(rr>2.))),'left_limb_lengths_rest_pose_m':[[float(np.linalg.norm(base0)),float(np.linalg.norm(base1))],[float(np.linalg.norm(knee_rel)),float(np.linalg.norm(ankle_rel))]]}
r['contact_geometry_pass']=r['left_actual_sole_low_mm']>=-1 and r['left_heel_actual_contact_area_mm2']>=9 and nt>=2 and at==0 and r['left_toe_low_mm']>=3 and r['left_bad_edges']==0
(P/'result.json').write_text(json.dumps(r,indent=2))
print(r,flush=True)
