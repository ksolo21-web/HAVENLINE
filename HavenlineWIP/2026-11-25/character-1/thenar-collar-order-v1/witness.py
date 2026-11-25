"""Exact C1 own-geometry cold grip bench; static interpolation snapshots only."""
import bpy,hashlib,math,numpy as np,json,os
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree
from collections import Counter
p=Path(__file__).resolve().parent
pin=Path(os.environ['C1_NARROW_READY_PACKET'])
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(pin/'SHA256SUMS')=='ccd17840ef942d61ba891958a50c7dcfe4b1f9a9263280667ce9dabb50c389d7'
for row in (pin/'SHA256SUMS').read_text().splitlines():
 h,n=row.split(maxsplit=1);assert sha(pin/n)==h
assert sha(Path(os.environ['C1_EXACT_BLEND']))=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
assert sha(Path(os.environ['C1_EXACT_GLB']))=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
g=Path(os.environ['C1_AXE_GLB'])
assert sha(g)=='79a3c9e4d31c609f0dc552b8810ab4061256def22e2eb9e4cefc3c1a33f3677e'
bpy.ops.wm.open_mainfile(filepath=str(pin/'c1-narrow-ready-witness.blend'))
rig=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
skin=next(x for x in bpy.context.scene.objects if x.type=='MESH')
assert len(rig.pose.bones)==52 and not bpy.data.actions
def vec(xs,k,n,d=np.float32):
 arr=np.empty(len(xs)*n,dtype=d);xs.foreach_get(k,arr);return arr.reshape(-1,n)
def tri(o):
 o.data.calc_loop_triangles();return vec(o.data.loop_triangles,'vertices',3,np.int32)
def poses():return vec(skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices,'co',3).astype(float)
P=vec(skin.data.vertices,'co',3).astype(float);F=tri(skin)
original=poses();names=[q.name for q in skin.vertex_groups]
lookup={n:i for i,n in enumerate(names)}
W=np.zeros((len(P),len(names)),np.float32)
for v in skin.data.vertices:
 for x in v.groups: W[v.index,x.group]=x.weight
dom=np.array(names)[W.argmax(1)]; X0=P[:,0];Y0=P[:,1];Z0=P[:,2]
_,weld=np.unique(np.rint(P/1e-6).astype('int64'),axis=0,return_inverse=True)
def make_bvh(arr, faces):
 ids,local=np.unique(faces.ravel(),return_inverse=True)
 return BVHTree.FromPolygons(arr[ids].tolist(),local.reshape(-1,3).tolist(),all_triangles=True,epsilon=0.)
def signed_planes(a,f):
 t=a[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
 h=(n*t[:,0]).sum(1); n[h<0]*=-1; h=abs(h)
 return n,h
# Body-first held orientation, not inferred from any former wrist or tool position.
# Normals oppose laterally on exact grip facets; digits aim forward, elbows support down and out.
import itertools
unit=lambda a:a/np.linalg.norm(a)
sides=('R','L')
mod={f'{n}.{s}' for n in ('upper_arm','forearm','hand') for s in sides}
for n in mod: rig.pose.bones[n].matrix_basis.identity()
bpy.context.view_layer.update()
rest_upper=poses()
fixed=P[:,2]<-.72
assert np.array_equal(rest_upper[fixed],original[fixed])
obs=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(g))
axe=next(o for o in bpy.context.scene.objects if o not in obs and o.type=='MESH')
A=vec(axe.data.vertices,'co',3).astype(float);T=tri(axe);assert len(T)==512
# Compact frontal diagonal, left tool end lower and handle center around sternum.
axis=unit(np.array([-.42,0.,.91]));r=unit(np.array([axis[2],0.,-axis[0]]))
M=np.column_stack((r,np.cross(axis,r),axis))
assert np.linalg.det(M)>.99999
factory=np.array([0.,0.,.223])+.18*axis
model=A@M.T+factory
# Absolute foreground separation from actual shell, no guessed capsule:
# only full bound on all non-arm triangles, not final clearance by shoulder/cuff.
arm=set(f'{n}.{s}' for s in sides for n in ('upper_arm','forearm','hand','clavicle'))
excluded=np.isin(dom,list(arm)) | (abs(X0)>.48)
garment=F[~excluded[F].any(1)]
# Use exact triangle XZ AABB overlap with projected complete tool AABB. Conservative, no body holes.
triXZ=rest_upper[garment][:,:,[0,2]]
slab=(triXZ.max(1)>=model[:,[0,2]].min(0)).all(1)&(triXZ.min(1)<=model[:,[0,2]].max(0)).all(1)
used=garment[slab]
assert len(used)
miny=float(rest_upper[used,1].min())
max_tool_y=float(model[:,1].max())
# Depth d is subtracted along actor Y. Strict finite 5mm foreground gap.
dmin=max_tool_y-miny+.005
constraints={};sets={}
for side,z,radius,radial in [('R',-.10,.071,-1),('L',-.26,.073,1)]:
 ix=np.flatnonzero(((abs(A[T,2]-z)<.05001)&(abs(np.linalg.norm(A[T,:2],axis=-1)-radius)<3e-5)).all(1));assert len(ix)==28
 plane,_=signed_planes(A,T[ix]);i=int(np.argmax(radial*plane[:,0]));fi=int(ix[i])
 face=A[T[fi]]
 # Interior facet target with known barycentric modest third coefficient.
 bary=np.array([.49,.49,.02]);ref=bary@model[T[fi]];outward=M@plane[i]
 h=rig.pose.bones['hand.'+side];bind=np.array(h.bone.matrix_local)
 coords=(P-bind[:3,3])@bind[:3,:3]
 patch=np.flatnonzero((W[:,lookup['hand.'+side]]>.8)&(abs(coords[:,0])<.025)&(abs(coords[:,1]-.061)<.012)&(coords[:,2]>0))
 assert len(patch)>30
 pi=int(patch[np.argmax(coords[patch,2])]);off=coords[pi]
 inward=-outward
 dvec=np.array([0.,-1.,.11 if side=='R' else -.11])
 forward=unit(dvec-inward*(dvec@inward)); hr=np.column_stack((np.cross(forward,inward),forward,inward))
 U,Q,H=(rig.pose.bones[f'{n}.{side}'] for n in ('upper_arm','forearm','hand'))
 shoulder=np.array(U.head)
 a=np.linalg.norm(np.array(Q.head)-shoulder);b2=np.linalg.norm(np.array(H.head)-np.array(Q.head))
 w0=ref+.0015*outward-hr@off
 dx,dy,dz=w0-shoulder
 # 20mm reserve requirement; inner shell separately checked after exact selection.
 delta2=(a+b2-.020)**2-dx*dx-dz*dz
 assert delta2>0.
 maxreach=float(dy+np.sqrt(delta2))
 minreach=float(dy-np.sqrt(delta2))
 constraints[side]={'reach_depth_interval_m':[minreach,maxreach],'shoulder':shoulder.tolist(),'links_m':[float(a),float(b2)],'surface_face_index':fi,'bary':bary.tolist(),'palm_vertex':pi,
  'palm_sample_count':len(patch),'grip_center_in_original_axis':z,'grip_face_z':float(bary@face[:,2]),'outward':outward.tolist()}
 sets[side]=(U,Q,H,a,b2,shoulder,w0,hr,pi,ref,outward,ix)
low=max(dmin,*(c['reach_depth_interval_m'][0] for c in constraints.values()))
high=min(c['reach_depth_interval_m'][1] for c in constraints.values())
result={'status':'HOLD_EMPTY_BILATERAL_CERTIFIED_DEPTH' if low>=high else 'STATIC_OPEN_EVALUATED','continuous_depth_interval_m':[low,high],'garment_foreground_min_m':dmin,
 'garment_witness_triangles':len(used),'sides':constraints,'unchanged_lower_to_parent_exact':True,
 'orientation':M.tolist(),'zero_depth_tool_origin':factory.tolist(),'negative_control_interval_after_extra_200mm_foreground_m':[low+.200,high]}
if low<high:
 # One stance, center of the demonstrably nonempty interval. No offset sweep.
 depth=(low+high)/2;dt=np.array([0,-depth,0]);TP=model+dt
 result['only_selected_depth_m']=depth
 def orient(m,a,b):
  q=(m.to_3x3()@Vector((0,1,0))).rotation_difference(Vector(b-a))
  h=(q.to_matrix()@m.to_3x3()).to_4x4();h.translation=Vector(a);return h
 for side,(U,Q,H,a,b2,sh,w0,hr,pi,ref,outward,ix) in sets.items():
  wr=w0+dt;v=wr-sh;length=np.linalg.norm(v);n=v/length
  assert abs(a-b2)<length<a+b2
  x=(a*a-b2*b2+length*length)/(2*length)
  pole=np.array([-.89 if side=='R' else .89,-.30,-.78]);pole=unit(pole-(pole@n)*n)
  el=sh+x*n+np.sqrt(a*a-x*x)*pole
  Um,Qm=U.matrix.copy(),Q.matrix.copy()
  U.matrix=orient(Um,sh,el);bpy.context.view_layer.update()
  Q.matrix=orient(Qm,el,wr);bpy.context.view_layer.update()
  h=Matrix(hr.tolist()).to_4x4();h.translation=Vector(wr);H.matrix=h;bpy.context.view_layer.update()
  constraints[side].update(wrist=wr.tolist(),elbow=el.tolist(),reserve_mm=float(1000*(a+b2-length)),
   forearm_to_hand_deg=float(np.degrees(np.arccos(np.clip(unit(wr-el)@hr[:,1],-1,1)))),
   wrist_error_mm=float(1000*np.linalg.norm(np.array(H.head)-wr)),elbow_error_mm=float(1000*np.linalg.norm(np.array(Q.head)-el)))
 base=poses();BT=make_bvh(TP,T)
 parent=Path(os.environ['C1_GLOVE_TOPOLOGY_RESULT'])
 assert sha(parent)=='dc4d419fc34dcf84ff3cd3bdf23d44306831b5fc3dfe5d7772ad45b90022533f'
 assert len(make_bvh(base,F).overlap(BT))==370
 # Clip at proximal cuff plane of the actual existing wrist. Intersections
 # are shared by original garment and replacement, including duplicated UV rows.
 ycut=-.018
 ring={};over={}
 for side,(U,Q,H,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  bind=np.array(H.bone.matrix_local); local=(P-bind[:3,3])@bind[:3,:3]
  D=local[:,1]-ycut
  # Distant head/body can extend across the infinite hand-local cut; restrict
  # ownership to the exact side's arm region, and fail any boundary there.
  sgn=-1 if side=='R' else 1
  owned=(sgn*P[:,0]>.52)
  up=(D>0)&owned
  cross=np.flatnonzero(up[F].any(1)&(~up[F]).any(1))
  out=np.flatnonzero(up[F].all(1))
  assert np.all(owned[F[cross]])
  edges={}; segments=[]
  for k in cross:
   row=F[k];tmp=[]
   for a,c in zip(row,np.roll(row,-1)):
    if up[a]==up[c]:continue
    a,c=sorted((int(a),int(c)));q=(a,c)
    if q not in edges:edges[q]=(-D[a]/(D[c]-D[a]),len(edges))
    tmp.append(edges[q][1])
   assert len(tmp)==2;segments.append(tmp)
  ee=np.asarray(list(edges),int);alpha=np.asarray([v[0] for v in edges.values()])
  K=P[ee[:,0]]*(1-alpha[:,None])+P[ee[:,1]]*alpha[:,None]
  C=base[ee[:,0]]*(1-alpha[:,None])+base[ee[:,1]]*alpha[:,None]
  Kloc=(K-bind[:3,3])@bind[:3,:3]
  # Only weld true geometric UV seams; no shell bridge at other endpoints.
  uk,rr,ww=np.unique(np.rint(K/1e-6).astype(int),axis=0,return_index=True,return_inverse=True)
  ss=np.unique(np.sort(ww[np.asarray(segments)],axis=1),axis=0);ss=ss[ss[:,0]!=ss[:,1]]
  nb={i:set() for i in range(len(uk))}
  for a,c in ss:nb[a].add(c);nb[c].add(a)
  bad=[i for i,x in nb.items() if len(x)!=2]
  loops=[]
  remain={i for i,x in nb.items() if x}
  while remain:
   start=min(remain);walk=[start]
   if any(len(nb[i])!=2 for i in remain):break
   prev=start;cur=min(nb[start])
   while cur!=start and len(walk)<=len(nb):
    walk.append(cur);nex=next(iter(nb[cur]-{prev}));prev,cur=cur,nex
   assert cur==start
   remain-=set(walk);loops.append(walk)
  over[side]={'cross_triangles':len(cross),'remove_triangles':len(out),'bad_degree':len(bad),'loops':[len(i) for i in loops],
   'bind_loop_ranges_local':np.ptp(Kloc,axis=0).tolist(),'exact_native_seam_neutral_mm':float(1000*np.max(np.linalg.norm(K-K[rr[ww]],axis=1))),
   'exact_native_seam_posed_mm':float(1000*np.max(np.linalg.norm(C-C[rr[ww]],axis=1)))}
  ring[side]=(ee,alpha,ww,rr,loops,cross,out,K,C,Kloc,up)
 print(json.dumps(over,indent=2),flush=True)
 # Exact connected distal shell labels. Small seam loops may be accessory
 # components; preserve them only if independent of the outer glove shell.
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 donor={}
 for side,(ee,aa,ww,rr,loops,cross,out,K,C,Kloc,up) in ring.items():
  fs=F[np.r_[cross,out]]
  ed=np.concatenate((fs[:,[0,1]],fs[:,[1,2]],fs[:,[2,0]]),axis=0)
  ii,jj=weld[ed].T
  # Distal welding only, all source rows incident on the cut retained.
  _,labels=connected_components(coo_matrix((np.ones(len(ii)),(ii,jj)),shape=(weld.max()+1,weld.max()+1)).tocsr(),directed=False)
  loop_cs=[int(labels[weld[ee[rr[loop[0]],0]]]) for loop in loops]
  pts=[Kloc[rr[L]][:,[0,2]] for L in loops]
  size=[float(np.ptp(x,axis=0).prod()) for x in pts]
  k=int(np.argmax(size))
  over[side]['loop_component_ids']=loop_cs;over[side]['outer_loop']=k
  over[side]['bounds_per_loop_mm']=[(1000*np.stack((x.min(0),x.max(0)))).tolist() for x in pts]
  over[side]['independent_other_seam_components']=all(c!=loop_cs[k] for i,c in enumerate(loop_cs) if i!=k)
  donor[side]=(k,loop_cs[k],labels)
 print(json.dumps(over,indent=2),flush=True)
 # No old wing heights or diagonals used. Pinned reached source boundary only.
 pp=Path(os.environ['C1_THENAR_ARCH'])
 assert sha(pp)=='3215b8841c347d1e93c8c5186cf79255e58385a64563229fa6d7ade66089be90'
 arch=np.load(pp)
 pp=Path(os.environ['C1_THENAR_CONSTRAINTS'])
 assert sha(pp)=='8447edaf86592e354a8321a337fac636416999a80f8b8e05bfa32733eca7e4b6'
 pp=Path(os.environ['C1_LEFT_COARSE_DATA'])
 assert sha(pp)=='bf3d6ae3a13f6160ab3f3cacbaca8d7891ffcf01f8c56ecd53275c63f2f0877e'
 olda=np.load(pp)
 pp=Path(os.environ['C1_INTRINSIC_PANELS'])
 assert sha(pp)=='6d9aae39e114ba17d0a30801293278e95a0bd9a4ec0126bbec1a9d2e366575d0'
 rails=np.load(pp)
 pp=(Path(os.environ['C1_LEFT_DISTAL_DATA'])/'editable_left_join.npz')
 assert sha(pp)=='c809dabd740a5cacab7ce5dff68b7fc50a5cde0f3c378ec6a9673a9eb1e0de6a'
 previous=np.load(pp)
 U,Q,H,*_,no,ix=sets['L'];a0=np.array(H.matrix);b0=np.array(H.bone.matrix_local)
 A=a0[:3,:3];B=b0[:3,:3]
 unpose=lambda v:(v-a0[:3,3])@A@B.T+b0[:3,3]
 exact=[93,94,95]
 old=arch['open'];bn=arch['bind']
 contact=old[exact];q=contact.mean(0)
 # Preserve exact previous independently pinned projection axes (using raw
 # pressure triangle's recorded topological orientation).
 rr=arch['actual_pressure_triangle'];xx=unit(old[rr[1]]-old[rr[0]])
 yy=unit(np.cross(no,xx))
 toxy=lambda v:1000*(v-q)@np.column_stack((xx+.60*no,yy))
 z=lambda v:1000*(v-q)@no
 out3=lambda x,y,z:q+.001*((x-.60*z)*xx+y*yy+z*no)
 keep=np.r_[np.arange(90),np.array(exact)]
 V=old[keep].tolist();P0=bn[keep].tolist();ids={int(i):j for j,i in enumerate(keep)}
 pA,pB,pC=[ids[i] for i in exact]
 D=[ids[i] for i in (85,82,79)]
 W=[ids[i] for i in (86,89,88,87)]
 def point(t):
  x=out3(*t);i=len(V);V.append(x.tolist());P0.append(unpose(x).tolist());return i
 # Collar rails are exterior to the exact pressure simplex. Independent
 # returns diverge on different edges, no shared internal diagonal from
 # previous rejected source.
 C1,C2,C3=map(point,[(24,8,7),(-40,8,7),(18,-16,7)])
 dport=point((17,-57,46))
 wlip,wwing=map(point,[(-88,-30,48),(-45,-40,39)])
 C=[C1,C2,C3]
 DS=[C1,C3,dport]+D
 WS=[C3,C2]+W+[wlip,wwing]
 X=toxy(np.asarray(V))
 def det(a,b):return float(a[0]*b[1]-a[1]*b[0])
 def area(t): 
  a=X[np.asarray(t)];return .5*sum(det(i,j) for i,j in zip(a,np.roll(a,-1,axis=0)))
 def incl(qt,a,b,c,e=1e-9):
  return min(det(b-a,qt-a),det(c-b,qt-b),det(a-c,qt-c))>=-e
 def orient(tri):
  return list(tri) if area(tri)>0 else list(tri)[::-1]
 def ear(poly):
  todo=list(poly);assert area(todo)>0
  out=[]
  while len(todo)>3:
   for i,b in enumerate(todo):
    a=todo[i-1];c=todo[(i+1)%len(todo)]
    if area([a,b,c])<=1e-8:continue
    if any(incl(X[j],X[a],X[b],X[c]) for j in todo if j not in (a,b,c)):continue
    out.append([a,b,c]);todo.pop(i);break
   else:raise ValueError('projected author sector is not a valid simple oriented polygon')
  out.append(todo)
  assert np.isclose(sum(area(t) for t in out),area(poly),atol=1e-7)
  return out
 # Actual assigned patch embedded as triangulated annulus (six faces)
 # with separately immersed actual contact, not duplicate tangent planes.
 assert all(incl(X[y],X[C1],X[C2],X[C3]) for y in (pA,pB,pC))
 core=[pA,pB,pC];assert area(core)>0
 collar=[]
 for i in range(3):
  j=(i+1)%3
  collar.extend(ear([C[i],C[j],core[j],core[i]]))
 assert all(area(t)>0 for t in collar)
 roles=['bearing']+['collar']*6
 dd=ear(DS);ww=ear(WS)
 faces=np.asarray([core]+collar+dd+ww)
 roles+=['dorsal_return']*len(dd)+['web_return']*len(ww)
 # Geometry feasibility before native creation: enumerate all pair
 # projected overlap polygons, preserving only shared edge/vertex contacts.
 def intersection(a,b):
  P=[x.copy() for x in X[a]]
  for i,j in zip(X[b],np.roll(X[b],-1,axis=0)):
   if not P:return 0.
   U=j-i;N=[]
   for x,y in zip(P,P[1:]+P[:1]):
    u=det(U,x-i);v=det(U,y-i)
    if u>=-1e-8:N.append(x)
    if (u>1e-8 and v<-1e-8) or (u<-1e-8 and v>1e-8):N.append(x+u/(u-v)*(y-x))
   P=N
  return abs(sum(det(i,j) for i,j in zip(P,P[1:]+P[:1])))*.5
 from itertools import combinations
 overlaps=[(i,j,intersection(faces[i],faces[j])) for i,j in combinations(range(len(faces)),2) if intersection(faces[i],faces[j])>1e-6]
 allpos=all(area(t)>1e-9 for t in faces)
 result={'status':'HOLD_PLANE_LAYOUT_NOT_FEASIBLE','actual_shell_native':False,'preauthored_separate_corridor_projected_overlaps':overlaps,
  'minimum_planar_triangle_area_mm2':min(area(t) for t in faces),'authored_sectors':{'dorsal':DS,'web':WS,'collar':C}}
 if not allpos or overlaps:
  (p/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result);raise SystemExit(0)
 # All faces are one single-valued oblique height graph. At any positive
 # projected distance from the defined joins, no face pairs share support.
 # Native run still required for all unmodeled surfaces of retained garment.
 tail=olda['sewn_dorsal_faces'];wf=olda['directional_left_web_tri']+86
 src=np.r_[tail,wf];N0=len(src)
 from collections import Counter
 def edgecount(m):return Counter((int(a),int(b)) for f in m for a,b in zip(f,np.roll(f,-1)))
 both=np.r_[src,faces];d=edgecount(both)
 approved=[(D[i],D[i+1]) for i in range(2)]+[(W[i],W[i+1]) for i in range(3)]+[(core[i],core[(i+1)%3]) for i in range(3)]
 assert all(d[i,j]==d[j,i]==1 for i,j in approved)
 # Check exact rejected non-boundary joins are no longer new edges.
 neu=edgecount(faces)
 banned=[(82,95),(79,95),(93,85),(94,88),(93,87)]
 assert all(neu[ids[i],ids[j]]+neu[ids[j],ids[i]]==0 for i,j in banned)
 VV=np.array(V);PP=np.array(P0)
 mesh=bpy.data.meshes.new('Left Exact Thenar separated material sectors')
 mesh.from_pydata(V,[],both.tolist());mesh.update()
 for mt in skin.data.materials:mesh.materials.append(mt)
 # Widened native diagnostic chart with 3 explicitly separate atlas islands.
 # Old certified near collar/wrist UVs stay exact, no promised palette pixels.
 uv=np.full((len(both),3,2),.5,np.float32);oldUV=olda['proximal_source_split_uv'];uv[:len(oldUV)]=oldUV
 for i,rol in enumerate(roles):
  ofs={'bearing':[.20,.23],'collar':[.20,.23],'dorsal_return':[.63,.39],'web_return':[.49,.65]}[rol]
  uv[N0+i]=np.array(ofs)+X[faces[i]]*.0016
 uvobj=mesh.uv_layers.new(name='Donor material and three split local charts')
 uvobj.data.foreach_set('uv',uv.ravel())
 Vn=vec(mesh.vertices,'co',3).astype(float)
 assert np.array_equal(Vn[:90],old[:90].astype(np.float32))
 assert np.array_equal(Vn[core],contact)
 bodyF=np.r_[F[previous['retained_source_faces']],previous['clipped_left_source_faces']]
 bodyV=np.r_[poses(),previous['open_additions']]
 BT=make_bvh(TP,T);bo=make_bvh(bodyV,bodyF)
 outer=make_bvh(rails['L_0_open'],rails['L_0_indices'])
 nested=make_bvh(olda['nested_open'],olda['nested_tri'])
 XF=make_bvh(Vn,faces);full=make_bvh(Vn,both)
 nh=XF.overlap(BT)
 pairs={(min(N0+i,j),max(N0+i,j)) for i,j in XF.overlap(full) if N0+i!=j and not np.isin(faces[i],both[j]).any()}
 bnr=lambda p,F:np.cross(p[F[:,1]]-p[F[:,0]],p[F[:,2]]-p[F[:,0]])
 N=bnr(Vn,faces);ori=bnr(PP,faces)@(A@B.T).T
 sd=(ori*N).sum(1)/np.maximum((ori*ori).sum(1),1e-30)
 E=np.unique(np.sort(np.r_[faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]],axis=1),axis=0)
 lr=lambda x:np.linalg.norm(x[E[:,1]]-x[E[:,0]],axis=1)
 e0=lr(Vn)/np.maximum(lr(PP),1e-12)
 faceid=constraints['L']['surface_face_index'];tf=TP[T[faceid]]
 ch=lambda u:(Vn[core]+u*no-tf[0])@no
 assert ch(-.002).max()<-.00199 and ch(.002).min()>.00199
 res={'actual_shell_native':True,'status':'HOLD_ANY_NONZERO_CLEARANCE_GATE_OR_FULL_ART',
  'actual_joined_local_triangles':len(both),'section_triangles':len(faces),'exact_two_face_seams':len(approved),
  'exact_contact_area_mm2':float(5e5*np.linalg.norm(N[0])),'signed_contact_max_abs_um':float(1e6*np.max(np.abs(ch(0.)))),
  'negative_embedded_max_mm':float(1000*ch(-.002).max()),'negative_gap_min_mm':float(1000*ch(.002).min()),
  'all_tool_surface_pairs':len(nh),'off_exact_face':sum(j!=faceid for i,j in nh),'off_band':sum(j not in ix for i,j in nh),
  'retained_source_pairs':len(XF.overlap(bo)),'nested_separate_pairs':len(XF.overlap(nested)),'near_exact_rail_pairs':len(XF.overlap(outer)),
  'nonadjacent_join_pairs':sorted(pairs),'all_native_area_fail':int(((sd<.5)|(sd>2.)).sum()),
  'reversals':int((sd<=0).sum()),'edge_fail':int(((e0<.5)|(e0>2.)).sum()),
  'right_and_full_default_unchanged':True,'full_glove_claim':False,'closure':False}
 result.update(res)
 np.savez_compressed(p/'editable_ordered_collar.npz',bind=PP,open=Vn,combined_local_triangles=both,sector_triangles=faces,sector_roles=np.asarray(roles),
  intrinsic_chart_xy_mm=X,corner_uv=uv,bearing_vertex_indices=core,owned_original_dorsal_vertex_indices=D,owned_original_web_vertex_indices=W)
 (p/'result.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(result,indent=2,default=lambda x:x.item()),flush=True)
