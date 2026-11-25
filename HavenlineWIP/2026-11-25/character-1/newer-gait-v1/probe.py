import bpy,numpy as np,hashlib,json,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
from mathutils.bvhtree import BVHTree
D=Path(__file__).resolve().parent
asset=D.parent/'c1-full-detail-rig-witness-repair-v2/c1-full-detail-rig-weight-repair-v2.blend'
master=D.parent/'c1-nov24-owner-v2/c1-meshy-ultra-multiview.glb'
assert hashlib.sha256(asset.read_bytes()).hexdigest()=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert hashlib.sha256(master.read_bytes()).hexdigest()=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
bpy.ops.wm.open_mainfile(filepath=str(asset))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
assert len(rig.pose.bones)==52 and not bpy.data.actions and all(b.matrix_basis.is_identity for b in rig.pose.bones)
assert np.array_equal(np.array(mesh.matrix_world),np.eye(4)) and np.array_equal(np.array(rig.matrix_world),np.eye(4))
U=bpy.context.view_layer.update
def vec(items,k,n,d=np.float32):
 a=np.empty(len(items)*n,dtype=d);items.foreach_get(k,a);return a.reshape(-1,n)
raw=vec(mesh.data.vertices,'co',3)
mi,ma=raw.min(0),raw.max(0)
center=np.array([.5*(mi[0]+ma[0]),.5*(mi[1]+ma[1]),mi[2]])
scale=1.75/(ma[2]-mi[2])
V0=(raw-center)*scale
def pts():
 return (vec(mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices,'co',3)-center)*scale
base=pts()
assert np.max(np.abs(base-V0))<.000001
z=V0[:,2]
xx,yy,_=V0.T
m=mesh.data;m.calc_loop_triangles()
tri=vec(m.loop_triangles,'vertices',3,np.int32)
E=vec(m.edges,'vertices',2,np.int32)
edgel=np.linalg.norm(V0[E[:,0]]-V0[E[:,1]],axis=1)
W=np.zeros((len(raw),len(mesh.vertex_groups)),dtype=np.float32)
for vi,v in enumerate(m.vertices):
 for g in v.groups:W[vi,g.group]=g.weight
lookup={g.name:g.index for g in mesh.vertex_groups}
B={b.name:b.matrix.copy() for b in rig.pose.bones}
tris={}; ids={}; pins={}; check_edges={}; K={}
v=.65; cadence=146.; step=v*60/cadence
for s,h in [('L',1),('R',-1)]:
 w=W[:,[lookup[n+'.'+s] for n in ('thigh','shin','foot','toe')]].sum(1)
 wf=W[:,[lookup[n+'.'+s] for n in ('foot','toe')]].sum(1)
 boot=(h*xx>.025)&(z<.38)&(wf>.35)
 ids[s]=np.flatnonzero(boot)
 f=-yy
 lowest=boot&(z<.040)
 outer=np.quantile(f[lowest],[.32,.68])
 for p in ('heel','toe'):
  sel=lowest&((f<=outer[0]) if p=='heel' else (f>=outer[1]))
  tris[s,p]=tri[sel[tri].all(1)]
  i=np.flatnonzero(sel)
  pins[s,p]=i[np.argsort(z[i])[:max(24,len(i)//15)]]
  assert len(tris[s,p])>50
 check_edges[s]=np.flatnonzero((w[E]>.92).all(1)&(z[E]<.43).all(1)&(edgel>.0008))
 K[s]=[B[n+'.'+s].translation.copy() for n in ('thigh','shin','foot','toe')]
rest=np.round(V0.astype(float),10)
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
def move(b,M):b.matrix=M;U()
def world(b):return (np.array(b.head)-center)*scale
def rawpoint(a):return Vector(np.array(a)/scale+center)
def rotate(deg):return Quaternion((1,0,0),math.radians(deg)).to_matrix().to_4x4()
def setj(b,mat):mat.translation=b.head;move(b,mat)
def leg(s,target,pitch,toe):
 t,sh,f,to=[rig.pose.bones[n+'.'+s] for n in ('thigh','shin','foot','toe')]
 A,B0,C,T=K[s];a=t.head.copy(); u=rawpoint(target)-a; dist=u.length
 l1=(B0-A).length;l2=(C-B0).length
 dc=min(dist,l1+l2-.003/scale);u.normalize()
 pole=Vector((.13 if s=='L' else -.13,-1.,0.))
 pole=(pole-u*pole.dot(u)).normalized()
 sn=(l1*l1-l2*l2+dc*dc)/(2*dc)
 k=a+u*sn+pole*math.sqrt(max(0.,l1*l1-sn*sn)); end=a+u*dc
 for j,old,new in ((t,B0-A,k-a),(sh,C-B0,end-k)):
  setj(j,old.rotation_difference(new).to_matrix().to_4x4()@B[j.name])
 setj(f,rotate(pitch)@B[f.name])
 setj(to,rotate(pitch+toe)@B[to.name])
 return float(np.linalg.norm(world(f)-target)),math.degrees((a-k).angle(end-k))
def boot_contact(s,p,t,pitch,toe,gap):
 anchor=base[pins[s,p]].mean(0)[:2].astype(float)
 wave=(-step/2 if s=='L' else step/2)+v*(t-.075)
 anchor+=np.array([0.,wave])
 target=world(rig.pose.bones['foot.'+s])+np.array([0.,wave,0.])
 for _ in range(4):
  leg(s,target,pitch,toe)
  x=pts()
  target+=np.r_[anchor-x[pins[s,p],:2].mean(0),gap-float(x[ids[s],2].min())]
 error,knee=leg(s,target,pitch,toe)
 return {'reach_mm':1000*error,'knee_internal_deg':knee,'pin_target_xy':anchor.tolist(),'pin_role':p,'pitch_deg':pitch,'digit_pitch_deg':toe}
def disjoint(x,Q):
 return BVHTree.FromPolygons(x.tolist(),Q.tolist(),all_triangles=True,epsilon=0.)
source_domains={}
for s,h in [('L',1),('R',-1)]:
 source_domains['boot'+s]=tri[((h*xx>.055)&(z<.42))[tri].all(1)]
 source_domains['knee'+s]=tri[((h*xx>.065)&(z>.425)&(z<.56))[tri].all(1)]
 source_domains['web'+s]=tri[((h*xx>.67)&(z>1.16)&(z<1.42))[tri].all(1)]
source_domains['cloth']=tri[((abs(xx)<.22)&(z>.61)&(z<.91))[tri].all(1)]
pairs=[('bootL','bootR'),('kneeL','kneeR')]+[(a+s,'cloth') for a in ('boot','knee','web') for s in ('L','R')]
def collide(x):
 tree={k:disjoint(x,t) for k,t in source_domains.items()}
 return {a+'-'+b:len(tree[a].overlap(tree[b])) for a,b in pairs}
bc=collide(base)
out=[]
for t,hip,L,R in [(0.,-.043,(-6.,0.,.006),(5.,-3.,.00015)),(.075,-.044,(-4.,0.,.00015),(8.,-5.,.00015)),(.15,-.041,(-2.,0.,.00015),(11.,-7.,.008))]:
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
 U();h=rig.pose.bones['hips'];p=B['hips'].copy()
 p.translation+=Vector((0,0,hip/scale));move(h,p)
 row={s:boot_contact(s,k,t,*angles) for s,k,angles in [('L','heel',L),('R','toe',R)]}
 x=pts()
 for s,p in [('L','heel'),('R','toe')]:
  arc,xy,n=area_contact(x,s,p)
  check=check_edges[s];q=E[check]
  er=np.linalg.norm(x[q[:,0]]-x[q[:,1]],axis=1)/edgel[check]
  pg=x[pins[s,p]].mean(0)
  row[s].update(min_boot_mm=1000*float(x[ids[s],2].min()), patch_area_mm2=arc*1e6,contact_faces=n,contact_geom_xy=xy.tolist() if xy is not None else None,edge_minmax=[float(er.min()),float(er.max())],edge_fail=int(sum((er<.5)|(er>2.))),guard_edges=len(er),material_pin_actual_xy=pg[:2].tolist(),opposite_pin_low_mm=1000*float(x[pins[s,'heel' if p=='toe' else 'toe'],2].min()))
 result={'t':t,'legs':row,'collisions':collide(x)}
 print(result,flush=True)
 out.append(result)
(Path(__file__).with_name('result.json')).write_text(json.dumps({'native':str(asset.name),'cadence_steps_per_min':cadence,'speed_m_s':v,'step_m':step,'neutral_collisions':bc,'domain_counts':{k:len(t) for k,t in source_domains.items()},'events':out},indent=2))
