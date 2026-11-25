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
frozen=P.parent/'hvn-l1-hero-contact-v1'/'samples.json'
d=json.loads(frozen.read_text())
assert d['asset_sha256']==sha
choice=d['result']['preset:biped:walk_Armature']; eligible=[]
for i,z in enumerate(choice['samples']):
 r=z['R'];l=z['L']
 separation=r['joints'][2][1]-l['joints'][2][1]
 if separation>.025 and r['heel'][2]-r['toe'][2]>.010:
  eligible.append((abs(r['toe'][2]),i))
_,idx=min(eligible)
assert idx==78 and choice['seconds'][idx]==.65
action=bpy.data.actions['preset:biped:walk_Armature']
full=choice['seconds'][-1]
start,stop=action.frame_range
fps=(stop-start)/full
assert abs(fps-round(fps))<1e-9
fr=start+.65*fps
ad.action=action
sc.frame_set(int(fr),subframe=fr%1)
update()
def point(s,key):return normpos(rig.pose.bones[s+'_'+key].head)
bonekeys=['Thigh','Calf','Foot','ToeBase']
R=rig.pose.bones['R_Thigh']
desc=[R]+list(R.children_recursive)
native={b.name:b.matrix_basis.copy() for b in desc}
src=norm(vertices(True))
assert np.max(np.abs(np.array([point('R',k) for k in bonekeys])-np.array(choice['samples'][idx]['R']['joints'])))<.00001
src_cent={k:src[masks['R'][k]].mean(0).tolist() for k in ('heel','toe')}
ad.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
update()
# Frozen left construction. Do not allow right solver, repositioning, or height changes.
L=rig.pose.bones['L_Thigh'];pel=rig.pose.bones['Hip']
swing=rot(-4)@B[L.name];swing.translation=B[L.name].translation
set_global(L,swing)
x=norm(vertices(True))
dz=.00015-float(x[ids['L'],2].min())
p=B[pel.name].copy();p.translation=local(normpos(p.translation)+np.array([0.,0.,dz]))
set_global(pel,p)
xl=norm(vertices(True))
frozen_lo=json.loads((P.parent/'hvn-l1-c1-compact-heel-v1.MbNjKL'/'result.json').read_text())
assert abs(dz*1000-frozen_lo['resulting_pelvis_delta_mm'][2])<.00001

for b in desc:b.matrix_basis=native[b.name]
update()
xy=norm(vertices(True))
lids=ids['L']
left_delta=float(np.max(np.linalg.norm((xl-xy)[lids],axis=1)))
assert left_delta<1e-6
def details(xyz,s):
 k=('L','R').index(s)
 er=edge[leg_edges[k]]; el=restedge[leg_edges[k]]
 rr=np.linalg.norm(xyz[er[:,0]]-xyz[er[:,1]],axis=1)/el
 return {'boot_min_mm':1000*float(xyz[ids[s],2].min()),'near':{n:dict(area_mm2=a*1e6,xy_m=None if uv is None else uv.tolist(),count=nt,lower_mm=float(xyz[masks[s][n],2].min())*1000,mean_mm=float(xyz[masks[s][n],2].mean())*1000) for n in ('heel','toe') for a,uv,nt in [area_contact(xyz,s,n)]},'guard_min_max':[float(rr.min()),float(rr.max())],'bad_edges':int(sum((rr<.5)|(rr>2.)))}
L=details(xy,'L'); Ri=details(xy,'R'); intrinsic=details(src,'R')
sh=(point('R','Foot')-point('R','Calf'))
rig_world=rig.matrix_world.to_quaternion()
foot=rig.pose.bones['R_Foot'].matrix.to_quaternion()
toe=rig.pose.bones['R_ToeBase'].matrix.to_quaternion()
o={'exact_clip':action.name,'sample_index_original_density_120':idx,'seconds':.65,'frame':fr,'native_fps':fps,'source_eligible_count':len(eligible),'source_matches_archived':True,'right_original':intrinsic,'right_original_centroids_m':src_cent,'right_applied_branch':sorted(native),'left':L,'right':Ri,'fixed_pelvis_z_mm':dz*1000,'left_boot_drift_m':left_delta,'right_stock_local_pose_error':max(float(np.max(np.abs(np.array(b.matrix_basis)-np.array(native[b.name])))) for b in desc),'right_shank_forward_lateral_deg':[math.degrees(math.atan2(-sh[1],-sh[2])),math.degrees(math.atan2(sh[0],-sh[2]))],'right_foot_world_quat':list(rig_world@foot),'right_foot_to_toe_quat':list((foot.inverted()@toe).normalized()),'right_ankle_behind_left_m':float(point('R','Foot')[1]-point('L','Foot')[1])}
o['split_numeric']=L['boot_min_mm']>=-1 and L['near']['heel']['area_mm2']>=9 and L['near']['toe']['lower_mm']>=3 and L['bad_edges']==0 and Ri['boot_min_mm']>=-1 and Ri['near']['toe']['area_mm2']>=9 and Ri['near']['heel']['lower_mm']>=3 and Ri['bad_edges']==0 and o['right_ankle_behind_left_m']>.025
(P/'result.json').write_text(json.dumps(o,indent=2))
print(o,flush=True)
