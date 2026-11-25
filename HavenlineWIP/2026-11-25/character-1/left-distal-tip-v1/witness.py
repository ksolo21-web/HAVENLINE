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
 packet=Path(os.environ['C1_LEFT_SIDE_DATA'])
 assert sha(packet)=='9dd15b5865f24f96b219cb525130191f7024b9e028112e619c8e15a25388756d'
 prev=np.load(packet)
 prevF=prev['combined_tri'];pre=prev['open'];bp=prev['bind'];uv0=prev['corner_uv']
 # One bounded distal cavity: oriented opposite three outer edges and five
 # measured dorsal/thenar continuation edges. No proximal body or nested cuff.
 outline=[98,97,100,99,84,85,96,95]
 distal=[(84,99),(99,100),(100,97)]
 rail=list(zip(outline,np.roll(outline,-1)))
 from collections import Counter
 def orient_edges(F):
  return Counter((int(i),int(j)) for f in F for i,j in zip(f,np.roll(f,-1)))
 old=orient_edges(prevF)
 assert all(old[int(j),int(i)]==1 and not old[int(i),int(j)] for i,j in rail)
 assert all(old[i,j]==1 for i,j in distal)
 U,Q,H,*_,no,ix=sets['L'];hr=np.array(H.matrix);br=np.array(H.bone.matrix_local)
 axis=hr[:3,:3];bindaxes=br[:3,:3]
 unskin=lambda x:(x-hr[:3,3])@axis@bindaxes.T+br[:3,3]
 xy=1000*pre[:,[1,2]]
 det=lambda x,y:float(x[0]*y[1]-x[1]*y[0])
 def signed(q):
  return .5*sum(det(i,j) for i,j in zip(xy[q],np.roll(xy[q],-1,axis=0)))
 if signed(outline)<0:xy[:,0]*=-1
 assert signed(outline)>1e-7
 def cross(a,b,c,d):
  return det(b-a,c-a)*det(b-a,d-a)<-1e-9 and det(d-c,a-c)*det(d-c,b-c)<-1e-9
 from itertools import combinations
 assert all(not cross(xy[a],xy[b],xy[c],xy[d]) for (a,b),(c,d) in combinations(rail,2) if len({a,b,c,d})==4)
 local=[];src=list(outline)
 while len(src)>3:
  for j,m in enumerate(src):
   a,c=src[j-1],src[(j+1)%len(src)]
   f=[a,m,c]
   if signed(f)<1e-8:continue
   if any(min(det(xy[y]-xy[x],xy[z]-xy[x]) for x,y in zip(f,np.roll(f,-1)))>=-1e-8 for z in src if z not in f):continue
   local.append(f);src.pop(j);break
  else:raise ValueError('bounded distal chart cannot be oriented')
 local.append(src)
 # One deliberately widened sparse rounded tip support; measured digit
 # positions select physical distal side of the already triangulated panel.
 anatomy=np.array([np.asarray(rig.pose.bones[x+'.L'].head) for x in ('index.02','middle.02','ring.02','pinky.02')])
 assert np.isfinite(anatomy).all()
 candidates=[(j,f) for j,f in enumerate(local) if set(f)&{99,100,84}]
 # Measure distal priority by actual finger axis and locations, not new angle.
 direction=axis[:,1]
 j,f0=max(candidates,key=lambda pair:float((pre[pair[1]].mean(0)-anatomy.mean(0))@direction))
 v0=pre[f0].mean(0)+np.array([.0035,0.,0.])
 V=np.r_[pre,[v0]];B=np.r_[bp,[unskin(v0)]]
 xy=np.r_[xy,[xy[f0].mean(0)]]
 k=len(V)-1
 local[j:j+1]=[[u,v,k] for u,v in zip(f0,np.roll(f0,-1))]
 Fa=np.asarray(local,int)
 assert all(signed(z)>1e-7 for z in Fa) and np.isclose(sum(signed(z) for z in Fa),signed(outline),atol=1e-7)
 joined=np.r_[prevF,Fa];counter=orient_edges(joined)
 assert all(counter[int(i),int(j)]==counter[int(j),int(i)]==1 for i,j in rail)
 # Chart draft inherits exact corner UV samples at source opposite edges.
 # Overlay controls which triangle corner belongs to which source chart.
 lookup={}
 for tri,uv in zip(prevF,uv0):
  for i,j in ((0,1),(1,2),(2,0)):
   lookup[(int(tri[i]),int(tri[j]))]=(uv[i],uv[j])
 Uv=np.empty((len(Fa),3,2),np.float32);lo=xy[outline].min(0);scale=np.ptp(xy[outline],axis=0)
 for e,face in enumerate(Fa):
  Uv[e]=[.56,.41]+np.array([.13,.16])*(xy[face]-lo)/scale
  chosen={}
  for i,j in ((0,1),(1,2),(2,0)):
   va,vb=int(face[i]),int(face[j])
   if (va,vb) in rail:
    exact=lookup[vb,va]
    for q,s in [(i,exact[1]),(j,exact[0])]:
     if q in chosen:assert np.array_equal(chosen[q],s)
     chosen[q]=s
  for q,s in chosen.items():Uv[e,q]=s
 uv=np.r_[uv0,Uv]
 mesh=bpy.data.meshes.new('Left spare distal closure of bounded open-shell arc')
 mesh.from_pydata(V.tolist(),[],joined.tolist());mesh.update()
 for mat in skin.data.materials:mesh.materials.append(mat)
 UVo=mesh.uv_layers.new(name='Source chart seams + local distal stock-palette chart')
 UVo.data.foreach_set('uv',uv.astype(np.float32).ravel())
 P=vec(mesh.vertices,'co',3).astype(float)
 assert np.array_equal(P[:len(pre)],pre)
 # Keep original opposite, exact retained torso/forearm and current axe.
 source=poses()
 saved=np.load((Path(os.environ['C1_LEFT_DISTAL_DATA'])/'editable_left_join.npz'))
 bO=np.r_[source,saved['open_additions']];bB=np.r_[np.array([v.co[:] for v in skin.data.vertices]),saved['bind_additions']]
 Bf=np.r_[F[saved['retained_source_faces']],saved['clipped_left_source_faces']]
 body=make_bvh(bO,Bf);bodyB=make_bvh(bB,Bf)
 TO=make_bvh(TP,T);NC=np.load(Path(os.environ['C1_LEFT_COARSE_DATA']))
 TN=make_bvh(NC['nested_open'],NC['nested_tri'])
 TN0=make_bvh(NC['nested_bind'],NC['nested_tri'])
 outer=np.load(Path(os.environ['C1_INTRINSIC_PANELS']))
 RO=make_bvh(outer['L_0_open'],outer['L_0_indices'])
 def hits(Vv):
  bvh=make_bvh(Vv,joined);cut=make_bvh(Vv,Fa);offset=len(prevF)
  ss={(min(i,j),max(i,j)) for i,j in bvh.overlap(bvh) if i!=j and not np.isin(joined[i],joined[j]).any()}
  return bvh,cut,sorted(ss)
 full,add,self0=hits(P);fB,aB,selfB=hits(B)
 alltool=full.overlap(TO);only=add.overlap(TO)
 fq=constraints['L']['surface_face_index']
 n=lambda A,Ff:np.cross(A[Ff[:,1]]-A[Ff[:,0]],A[Ff[:,2]]-A[Ff[:,0]])
 n0=n(B,Fa)@(axis@bindaxes.T).T;n1=n(P,Fa)
 ratio=(n0*n1).sum(1)/np.maximum((n0*n0).sum(1),1e-20)
 Ue=np.unique(np.sort(np.r_[Fa[:,[0,1]],Fa[:,[1,2]],Fa[:,[2,0]]],axis=1),axis=0)
 ol=lambda x:np.linalg.norm(x[Ue[:,1]]-x[Ue[:,0]],axis=1)
 er=ol(P)/np.maximum(ol(B),1e-10)
 ti=P[Fa[np.linalg.norm(n1,axis=1).argmax()]];q=ti.mean(0);nn=unit(np.cross(ti[1]-ti[0],ti[2]-ti[0]));xx=unit(ti[1]-ti[0])
 imp=np.stack([q-.001*nn-.0001*xx,q+.001*nn-.0001*xx,q+.0001*xx])
 neg=len(make_bvh(imp,np.array([[0,1,2]])).overlap(add));assert neg>0
 signed_face=float(np.max(np.abs((P[prev['source_exact_pressure']]-TP[T[fq]][0])@no)))
 out={'status':'HOLD_UNTIL_COMPLETE_LEFT_AND_INDEPENDENT','new_faces':len(Fa),'old_faces_exact':len(prevF),'joined_local_faces':len(joined),
   'locked_3_tip_edges':distal,'outer_or_bounded_dorsal_two_face_edges':len(rail),'same_old_uv_geometry':True,
   'native_tool_pairs_new':len(only),'tool_pairs_exact_existing_assigned_face':sum(j==fq for i,j in alltool),
   'tool_pairs_off_exact':sum(j!=fq for i,j in alltool),'tool_pairs_off_band':sum(j not in ix for i,j in alltool),
   'bearing_signed_error_m':signed_face,'open_nonadjacent_pairs':self0,'rest_nonadjacent_pairs':selfB,
   'new_open_retained':len(add.overlap(body)),'whole_local_open_retained':len(full.overlap(body)),
   'new_neutral_retained':len(aB.overlap(bodyB)),
   'new_open_nested_pairs':len(add.overlap(TN)),'new_neutral_nested_pairs':len(aB.overlap(TN0)),'new_open_outer_rail_pairs':len(add.overlap(RO)),
   'signed_edge_fail':int(((er<.5)|(er>2.)).sum()),'signed_face_fail':int(((ratio<.5)|(ratio>2.)).sum()),'reversals':int((ratio<=0).sum()),
   'negative_transverse_pairs':neg,'no_mirror_closure_or_full_shell':True,'distal_landmarks_actor':anatomy.tolist()}
 np.savez_compressed(p/'editable_distal_tip.npz',bind=B,open=P,combined_tri=joined,distal_patch_tri=Fa,corner_uv=uv,author_boundary=outline,
  outer_locked_edges=np.asarray(distal),web_unchanged_source=prev['source_open_web'],exact_pressure_source=prev['source_exact_pressure'])
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
