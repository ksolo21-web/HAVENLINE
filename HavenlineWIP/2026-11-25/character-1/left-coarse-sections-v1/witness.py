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
 rails=Path(os.environ['C1_INTRINSIC_PANELS'])
 assert sha(rails)=='6d9aae39e114ba17d0a30801293278e95a0bd9a4ec0126bbec1a9d2e366575d0'
 rr=np.load(rails)
 previous=Path(os.environ['C1_LEFT_DISTAL_DATA'])
 assert sha(previous/'editable_left_join.npz')=='c809dabd740a5cacab7ce5dff68b7fc50a5cde0f3c378ec6a9673a9eb1e0de6a'
 U,Q,H,_,_,_,_,_,_,_,no,ix=sets['L']
 Hp=np.array(H.matrix);Hb=np.array(H.bone.matrix_local);R=Hp[:3,:3];R0=Hb[:3,:3]
 def loc(V,H):return (V-H[:3,3])@H[:3,:3]
 def to(V,H):return V@H[:3,:3].T+H[:3,3]
 def at(name,rig,kind):return np.asarray(getattr(rig[name+'.L'],kind),dtype=float)
 ppose=rig.pose.bones;prest=rig.data.bones
 def row(what,frame,kind):return loc(np.array([at(s,what,kind) for s in ['index.01','middle.01','ring.01','pinky.01']]),frame)
 kb=row(prest,Hb,'head_local'); ko=row(ppose,Hp,'head')
 assert np.max(np.linalg.norm(kb-ko,axis=1))<1e-5
 # Explicit named sectional design. Anatomical dorsum is sign opposite the
 # actual palmar facing inward axis; no angular rail interpolation.
 A=rr['L_0_open'];Ab=rr['L_0_bind'];n0=len(A)//2
 X=loc(A[n0:],Hp); Xr=loc(Ab[n0:],Hb)
 ax=np.asarray(no)@R
 dorsal_sign=np.sign(ax[2]);assert dorsal_sign<0
 # Three source anchors on the true dorsal far seam at fixed fraction of
 # knuckle width. Selection uses measured x and dorsal half only.
 order=np.argsort(ko[:,0]); kw=ko[order]
 xs=np.array([.85*kw[0,0]+.15*kw[-1,0],kw[:,0].mean(),.15*kw[0,0]+.85*kw[-1,0]])
 dorsal=np.flatnonzero(dorsal_sign*(X[:,2]-np.median(X[:,2]))>0)
 ix0=[int(dorsal[np.argmin(np.abs(X[dorsal,0]-x) + .45*(X[dorsal,2]-np.min(X[dorsal,2])))]) for x in xs]
 assert len(np.unique(ix0))==3
 B0=Xr[ix0];O0=X[ix0]
 # Three artist-selected chamber cross-sections of the existing
 # glove-sized dorsal hand envelope. No thumb/palm points projected from mesh.
 yt=float(kw[:,1].mean()); Xs=xs.copy()
 K=np.stack([np.array([x,yt,float(kw[:,2].mean())+dorsal_sign*cap]) for x,cap in zip(Xs,[.024,.030,.025])])
 M=np.stack([np.array([x,.53*yt,dorsal_sign*cap]) for x,cap in zip(Xs,[.028,.034,.028])])
 ytip=np.minimum(np.asarray([.133,.140,.132]),yt+.05)
 ridge=np.stack([np.array([x*.83,y,float(kw[:,2].mean())+dorsal_sign*cap]) for x,y,cap in zip(Xs,ytip,[.018,.022,.018])])
 Dbind=to(np.r_[B0,M,K,ridge],Hb); Dopen=to(np.r_[O0,M,K,ridge],Hp)
 # The crown flows from left to right and proximal to distal for every quad.
 Df=[]; charts=[]
 for i in range(3):
  for j in range(2):
   a=3*i+j;c=a+3

   Df.extend([[a,c,c+1],[a,c+1,a+1]])
   charts.extend([i,i])
 Df=np.asarray(Df,int)
 # Independent cuff branch follows exact 48-edge far loop with one measured
 # deeply bounded local extension. It is never joined to the dorsal cavity.
 nested=rr['L_1_open']; nb=rr['L_1_bind'];k=len(nested)//2
 assert k==48
 nO=nested[k:]; nB=nb[k:]
 t=.003
 nopen=np.r_[nO,nO+t*R[:,1]]; nbind=np.r_[nB,nB+t*R0[:,1]]
 NF=np.array([[i,(i+1)%k,(i+1)%k+k] for i in range(k)]+[[i,(i+1)%k+k,i+k] for i in range(k)])
 # Source UVs paired per-corner across all split charts. Continuation radial
 # offset is marked independent experimental chart, not wardrobe texturing.
 old=rr['L_1_uv'];Nuv=np.empty_like(old)
 for hh in range(2):
  for j in range(k):
   z=old[j]
   a,be=z[0],z[2];d=.37*(be-a)
   Nuv[hh*k+j]=[be,old[(j+1)%k,2],old[(j+1)%k,2]+d] if hh==0 else [be,old[(j+1)%k,2]+d,be+d]
 # Isolated pressure and web floats serve as explicit fixed pose witnesses.
 # Not a "joined glove" and not physically closing.
 bp=rr['L_exact_bearing_target'];wp=rr['left_web_open_anchors'];wb=rr['left_web_bind_anchors']
 q=bp.mean(0);bd=np.r_[bp,bp+.003*no]
 BF=np.array([[0,2,1],[3,4,5],[0,1,4],[0,4,3],[1,2,5],[1,5,4],[2,0,3],[2,3,5]])
 WF=rr['left_web_indices']
 base=poses()
 # Retained body separation and full shaft are both actual source.
 joint=np.load(previous/'editable_left_join.npz')
 wcp=joint['clipped_left_source_faces']
 combined=np.r_[base,joint['open_additions']]
 proxy_faces=np.concatenate((F[joint['retained_source_faces']],wcp))
 body=make_bvh(combined,proxy_faces);tool=make_bvh(TP,T)
 def native(name,V,f):
  m=bpy.data.meshes.new(name)
  m.from_pydata(V.tolist(),[],f.tolist());m.update()
  for mat in skin.data.materials:m.materials.append(mat)
  return vec(m.vertices,'co',3).astype(float)
 records={}
 def read(name,V,B,f):
  x=native('Coarse-'+name,V,f)
  y=native('Coarse-'+name+'-bind',B,f)
  X=make_bvh(x,f)
  nn=lambda z:np.cross(z[f[:,1]]-z[f[:,0]],z[f[:,2]]-z[f[:,0]])
  aa=nn(y)@(R@R0.T).T; aa2=nn(x);den=(aa*aa).sum(1)
  rates=(aa*aa2).sum(1)/np.maximum(den,1e-24)
  E=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0)
  ll=lambda d:np.linalg.norm(d[E[:,1]]-d[E[:,0]],axis=1)
  er=ll(x)/np.maximum(ll(y),1e-10)
  selfp=sum(1 for i,j in X.overlap(X) if i<j and not np.isin(f[i],f[j]).any())
  # Count entire whole body, discriminating outer rail seams via vertex exactness.
  mints=X.overlap(body);coll=[]
  for i,j in mints:
   delta=np.linalg.norm(x[f[i]][:,None]-combined[proxy_faces[j]][None],axis=-1)
   if delta.min()>1e-7:coll.append((i,j))
  hit=X.overlap(tool)
  records[name]={'faces':len(f),'signed_face_bad':int(((rates<.5)|(rates>2.)).sum()),'face_reversal':int((rates<=0).sum()),'edge_bad':int(((er<.5)|(er>2.)).sum()),
   'nonadj_self':selfp,'retained_nonshared_pairs':len(coll),'tool_pairs':len(hit),'off_grip_band':sum(j not in ix for i,j in hit)}
  return x,X
 _,D=read('hand_authored_dorsum',Dopen,Dbind,Df)
 _,J=read('inner_cuff_local',nopen,nbind,NF)
 _,W=read('four_exact_web',wp,wb,WF)
 _,T0=read('three_exact_pressure_edges',bd,to(loc(bd,Hp),Hb),BF)
 local={'dorsal_to_web':len(D.overlap(W)),'dorsal_to_cuff':len(D.overlap(J)),
        'dorsal_to_pressure':len(D.overlap(T0)),'web_to_pressure':len(W.overlap(T0)),
        'inner_cuff_to_pressure':len(J.overlap(T0))}
 # Gauge negative with a real transverse intrusion, not coplanar BVH.
 a=Dopen[Df[3]];mid=a.mean(0);n=unit(np.cross(a[1]-a[0],a[2]-a[0]));ex=unit(a[1]-a[0])
 neg=np.stack([mid-.001*n-.0001*ex,mid+.001*n-.0001*ex,mid+.0002*ex])
 assert len(make_bvh(neg,np.array([[0,1,2]])).overlap(D))>0
 out={'status':'HOLD_COARSE_LOCAL_ONLY','native_sections':records,'mutual_pairs':local,
  'exact_assigned_left_surface_area_mm2':float(5e5*np.linalg.norm(np.cross(bp[1]-bp[0],bp[2]-bp[0]))),
  'independent_nested_source_endpoints':k,'unambiguously_non_crossing_sparse_sections':bool(len(set(ix0))==3 and np.all(np.diff(xs)>0)),
  'source_bound_dorsal_points':ix0,'source_thumb_web_roles_exact':True,
  'coarse_whole_sewn_upper_executed':False,'right_unchanged':True,'closure':False}
 # One actual exact proximal subjoin. Resolve only the measured dorsal
 # cut arc. Stitch both spans to the coarse M edge; no full ring or cavity.
 source_idx=[(ix0[0]-j)%n0 for j in range((ix0[0]-ix0[-1])%n0+1)]
 mididx=source_idx.index(ix0[1]);assert len(source_idx)==77
 m=len(source_idx); dB=np.r_[Ab[n0+np.array(source_idx)],Dbind[3:]]
 dO=np.r_[A[n0+np.array(source_idx)],Dopen[3:]]
 cf=[]; cfuv=[]
 def fadd(tri,uv0):cf.append(tri);cfuv.append(uv0)
 fx=rr['L_0_indices'];ux=rr['L_0_uv']
 UVedge={}
 for tri,tex in zip(fx,ux):
  for i,j in [(0,1),(1,2),(2,0)]:
   if tri[i]>=n0 and tri[j]>=n0:UVedge[(int(tri[i]-n0),int(tri[j]-n0))]=(tex[i],tex[j])
 meduv=[]
 for i0,i1,j in [(0,mididx,0),(mididx,m-1,1)]:
  aa=UVedge[(source_idx[i0],source_idx[i0+1])][0]
  bb=UVedge[(source_idx[i1-1],source_idx[i1])][1]
  begin=np.asarray(aa)+[0.,.014];end=np.asarray(bb)+[0.,.014]
  fadd([i0,m+j,m+j+1],[aa,begin,end])
  for k0 in range(i0,i1):
   a0,b0=UVedge[(source_idx[k0],source_idx[k0+1])]
   fadd([k0,k0+1,m+j+1],[a0,b0,end])
  meduv.append(begin)
 meduv.append(end)
 zcf=np.array(cf,int)
 # For both authored flat-pair sections accounting, orient each original far
 # edge oppositely and verify exact per-corner split values at all junctions.
 assert all(np.array_equal(cfuv[1+i][0],UVedge[(source_idx[i],source_idx[i+1])][0]) for i in range(mididx))
 tail=[list(np.asarray(t,int)-3+m) for t in Df[4:]]
 ready_faces=np.r_[zcf,tail][:,::-1];cfuv=np.asarray(cfuv)[:,::-1]
 zn,parts=read('dorsal_exact_arch_subjoin',dO,dB,ready_faces)
 # Every sewn coarse far edge has exactly one source strip edge and one
 # new panel edge with opposing orientation (not a topological coincidence).
 ordered_edges={(int(a),int(b)) for face in ready_faces for a,b in zip(face,np.roll(face,-1))}
 assert all((i+1,i) in ordered_edges for i in range(m-1))
 assert all((source_idx[i],source_idx[i+1]) in UVedge for i in range(m-1))
 out['dorsal_sewn_arc']={'source_edges':m-1,'uv_corner_pairs':2*(m-1),'all_opposite_oriented_and_two_incident':True}
 out['native_sections']=records
 out['sewn_arc_mutual_pairs']={'web':len(parts.overlap(W)),'inner_cuff':len(parts.overlap(J)),'bearing':len(parts.overlap(T0))}
 np.savez_compressed(p/'editable_left_coarse.npz',dorsal_bind=Dbind,dorsal_open=Dopen,dorsal_tri=Df,dorsal_charts=charts,
  original_L0_dorsal_farrail_rows=ix0,nested_bind=nbind,nested_open=nopen,nested_tri=NF,nested_uv=Nuv,
  directional_left_web_bind=wb,directional_left_web_open=wp,directional_left_web_tri=WF,
  locked_left_bearing=bp,bearing_fixture_indices=BF,proximal_exact_source_rows=source_idx,sewn_dorsal_bind=dB,sewn_dorsal_open=dO,sewn_dorsal_faces=ready_faces,proximal_source_split_uv=np.asarray(cfuv))
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda a:a.item())+'\n');print(json.dumps(out,indent=2,default=lambda a:a.item()),flush=True)
