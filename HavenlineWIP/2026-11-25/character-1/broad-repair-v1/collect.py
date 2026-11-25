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
from mathutils.bvhtree import BVHTree
T=.15; vel=.80; cadence=150.; step=vel*60/cadence
# Set real diagonal knee aim via the native rest shank plane, not the prior artificial fixed pole.
def leg(s,target,pitch,dig):
 thigh,calf,foot,toe=[rig.pose.bones[s+'_'+j] for j in ('Thigh','Calf','Foot','ToeBase')]
 a=thigh.head.copy(); A,Bb,C=(B[b.name].translation for b in (thigh,calf,foot))
 seg1=Bb-A;seg2=C-Bb;l1=seg1.length;l2=seg2.length
 axis=local(target)-a; req=axis.length; maxlen=l1+l2-.003/scale
 dist=min(req,maxlen); u=axis.normalized()
 r=(C-A).normalized()
 native=(seg1-r*seg1.dot(r)).normalized()
 # Add authored anterior direction rather than amplifying the slight, inward stock rest component.
 front=worldrot.inverted()@Vector((.10 if s=='L' else -.10,-1.,0.))
 q=(front-u*front.dot(u)).normalized()
 # Keep the actual worldsigned anatomy; pure shortest-swing rotation leaves original twist scale/weights intact.
 v=(native-u*native.dot(u)).normalized()
 if v.dot(q)<.0:v=q
 pole=(.65*q+.35*v).normalized()
 x=(l1*l1-l2*l2+dist*dist)/(2*dist)
 k=a+u*x+pole*math.sqrt(max(0.,l1*l1-x*x));n=a+u*dist
 for obj,bas,want in ((thigh,seg1,k-a),(calf,seg2,n-k)):
  at(obj,bas.rotation_difference(want).to_matrix().to_4x4()@B[obj.name])
 at(foot,rot(pitch)@B[foot.name]);at(toe,rot(pitch+dig)@B[toe.name])
 return float(np.linalg.norm(normpos(foot.head)-target))
def choose_pin(s,p):
 return rest[masks[s][p]].mean(0)[:2]+np.array([0.,-step/2 if s=='L' else step/2])
pins={s:choose_pin(s,p) for s,p in [('L','heel'),('R','toe')]}
# Near-floor term based on lowest actual evaluated outer sole; XY is tied to the same material rows
# so phase-to-phase translation cannot hide skating of that tracked patch.
def solve_support(s,surface,pitch,dig,t,clearance):
 site=pins[s]+np.array([0.,vel*(t-T/2)])
 target=normpos(B[s+'_Foot'].translation)+np.array([0.,(-step/2 if s=='L' else step/2)+vel*(t-T/2),-.015])
 for i in range(5):
  leg(s,target,pitch,dig); obs=norm(vertices(True))
  actual=obs[masks[s][surface]].mean(0)
  target[:2]+=site-actual[:2]
  target[2]+=clearance-float(obs[ids[s],2].min())
 return target,leg(s,target,pitch,dig),site.tolist()
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
heel_masks={v:masks[v]['heel'] for v in ('L','R')}
def trmask(side):
 w=sum(W.get(side+'_'+j,0) for j in ('Foot','ToeBase','Calf','CalfTwist01','CalfTwist02'))
 return tri[(w[tri]>.70).all(1)&(rest[tri,2].max(1)<.37)]
lboot,rboot=trmask('L'),trmask('R')
w=sum(w for k,w in W.items() if k in ('Waist','Spine01','Spine02','CoatFront','L_CoatFront','PouchSwing') or k.startswith('HemFastener_'))
coat=tri[(w[tri]>.75).all(1)&(rest[tri,2].min(1)>.31)&(rest[tri,2].max(1)<.75)]
assert min(map(len,(lboot,rboot,coat)))>10
def overlaps(x,p,q):
 ax=BVHTree.FromPolygons(x.tolist(),p.tolist(),all_triangles=True,epsilon=0)
 bx=BVHTree.FromPolygons(x.tolist(),q.tolist(),all_triangles=True,epsilon=0)
 return len(ax.overlap(bx))
out=[]
frames=[]; pose_matrices=[]; skin_world=[]
for t,hip,l,rp in [
(.000,-.044,(-7.,0.,.007),(6.,-3.,.00015)),
(.075,-.045,(-4.,0.,.00015),(10.,-6.,.00015)),
(.150,-.042,(-2.,0.,.00015),(12.,-7.,.009))
]:
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 update()
 hipb=rig.pose.bones['Hip']; Q=B[hipb.name].copy()
 Q.translation=local(normpos(Q.translation)+np.array([0.,0.,hip]))
 set_global(hipb,Q)
 want={}
 for s,k,angles in [('L','heel',l),('R','toe',rp)]:
  target,err,site=solve_support(s,k,*angles[:2],t,angles[2])
  want[s]={'target':target.tolist(),'reach_mm':err*1000,'site':site,'surface':k,'height_target':angles[2],'foot_toe_rel_deg':angles[1]}
 xyz=norm(vertices(True))
 frames.append(xyz.copy())
 pose_matrices.append([np.array(b.matrix_basis) for b in rig.pose.bones])
 skin_world.append([np.array(rig.matrix_world@rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@rig.matrix_world.inverted()) if n in rig.pose.bones else np.eye(4) for n in sorted(W)])
 for s,c in want.items():
  k=c['surface'];i=('L','R').index(s);eg=edge[leg_edges[i]]
  rat=np.linalg.norm(xyz[eg[:,0]]-xyz[eg[:,1]],axis=1)/restedge[leg_edges[i]]
  area,real,cnt=area_contact(xyz,s,k)
  delta=xyz[masks[s][k]].mean(0)[:2]-c['site']
  opp='toe' if k=='heel' else 'heel'
  c.update(position_phase_m=xyz[masks[s][k]].mean(0).tolist(),anchor_foreaft_error_mm=float(delta[1]*1000),anchor_lateral_error_mm=float(delta[0]*1000),contact_area_mm2=area*1e6,contact_faces=cnt,contact_site_xy=None if real is None else real.tolist(),opposite_lift_mm=float(xyz[masks[s][opp],2].min())*1000,lowest_boot_mm=float(xyz[ids[s],2].min())*1000,edge_minmax=[float(rat.min()),float(rat.max())],bad_guard_edges=int(sum((rat<.5)|(rat>2.))))
 clash={'left_right':overlaps(xyz,lboot,rboot),'left_coat':overlaps(xyz,lboot,coat),'right_coat':overlaps(xyz,rboot,coat)}
 print(t,want,clash,flush=True)
 out.append({'t':t,'pelvis_mm':1000*hip,'phase':want,'overlap_pairs':clash})
data={'source':sha,'speed_m_s':vel,'cadence_steps_per_min':cadence,'step_m':step,'projected_cycle_s':120/cadence,'axis_forward':'-Y','samples':out,'collision_domains':[len(lboot),len(rboot),len(coat)],'baseline_overlap':[overlaps(rest,lboot,rboot),overlaps(rest,lboot,coat),overlaps(rest,rboot,coat)]}

# Same controls, bilateral evaluated mesh arrays only. No weights or asset edit.
np.savez_compressed(P/'pose-inputs.npz',rest=rest,xyz=np.stack(frames),pose_matrices=np.array(pose_matrices),skin_world=np.array(skin_world),scale=scale,offset=offset,edge=edge,tri=tri,
 left_ids=leg_edges[0],right_ids=leg_edges[1],lboot=lboot,rboot=rboot,coat=coat,
 bootL=ids['L'],bootR=ids['R'],
 contactL=tris['L','heel'],contactR=tris['R','toe'],
 phaseL=masks['L']['heel'],phaseR=masks['R']['toe'],
 weights=np.array([W[k] for k in sorted(W)]),weight_names=sorted(W))
(P/'source_reproduced.json').write_text(json.dumps(data,indent=2))
