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
 # Keep prior exact cut and target bearing, but neither previous zipper
 # orientation nor its foldback surface. Construct intrinsic material strips
 # from each source edge's own UV chart, then use local separate corridors.
 src=Path(os.environ['C1_STITCHED_CUFF_DATA'])
 assert sha(src/'editable_splice.npz')=='5814ad91f1757e9e4622f8f58999c62aef72267dc63152bf43d67985c556f886'
 assert sha(src/'result.json')=='f284a3b50abbfa8d8f40b9206e5e18ff0e91b4ce158a7f9a934438271dabff7a'
 joint=np.load(src/'editable_splice.npz'); parents=json.loads((src/'result.json').read_text())
 source=Path(os.environ['C1_CONTACT_DATA'])
 assert sha(source)=='14d72f4122ddd370663d1c25ea2560e4c79b0fde672f1a8ce4db207f2f0329d4'
 fixture=np.load(source)
 Bs=np.r_[P,joint['new_bind']]; Os=np.r_[poses(),joint['new_open']]
 upstream=np.concatenate([F[joint['source_keep']],joint['clipped_source_faces']])
 orig_uv=joint['clipped_source_corner_uv']; clipF=joint['clipped_source_faces']
 BT=make_bvh(TP,T); body=make_bvh(Os,upstream)
 assert not body.overlap(BT)
 lookup_clipped={}
 for fj,(face,uv0) in enumerate(zip(clipF,orig_uv)):
  for i,j in ((0,1),(1,2),(2,0)):
   if face[i]>=len(P) and face[j]>=len(P):
    lookup_clipped[(int(face[i]),int(face[j]))]=(uv0[i],uv0[j],fj)
 # Deliberate left anatomical side before any pattern triangles. The span
 # follows the source thumb root, thumb end of first phalanx and index root
 # longitudinal creases, using their exact named transformations.
 def named(side,rest):
  get=rig.data.bones if rest else rig.pose.bones
  def h(x):
   z=get[x+'.'+side]; return np.asarray(z.head_local if rest else z.head,dtype=float)
  root=h('thumb.01'); t=h('thumb.02'); i=h('index.01'); middle=h('middle.01')
  root2=root+.60*(t-root)
  ridge=.44*t+.56*i
  at=.76*i+.24*middle
  return np.stack((root2,ridge,at,root*.50+i*.50))
 web_b=named('L',True);web_o=named('L',False)
 assert np.linalg.norm(web_b[2]-web_b[0])>.03
 materials=bpy.data.meshes.new('Intrinsic-cloth-rails-native')
 skin.data.calc_loop_triangles()
 result={'status':'HOLD_UNLESS_COMPLETE_LOCAL_PANEL_AND_ANATOMICAL_WEB','retained_source_clearance_pairs':0,'hands':{}}
 geom={}; allpan=[]
 for side,(U,Q,H,_,_,_,_,hr,pi,ref,n,ix) in sets.items():
  seq=np.array(joint[side+'_seam']); offset=np.cumsum([0]+parents['hands'][side]['seam_lengths'])
  bindf=np.array(H.bone.matrix_local);holdf=np.array(H.matrix)
  rb=bindf[:3,:3];ro=holdf[:3,:3]
  info=[];sidel=[]
  for k in range(len(offset)-1):
   ids=seq[offset[k]:offset[k+1]]
   p0=Bs[ids]; p1=Os[ids]; L=len(ids)
   leng=np.linalg.norm(np.roll(p0,-1,axis=0)-p0,axis=1)
   assert min(leng)>1e-8
   intrinsic=np.r_[0,np.cumsum(leng)]
   # Independent physical short pattern lengths; exact seam charts and
   # shell corridors share the arm direction, no nested route crosses from
   # its old UV rail to a different chart point. First local panel only.
   width=.008 if k==0 else [.0055,.0045][k-1]
   elbow=np.asarray(Q.head);wr=np.asarray(H.head)
   vb=rb[:,1];vo=ro[:,1]
   p2=p0+width*vb;p3=p1+width*vo
   N=len(p0)
   f=np.array([[i,(i+1)%N,(i+1)%N+N] for i in range(N)]+[[i,(i+1)%N+N,i+N] for i in range(N)])
   z0=np.r_[p0,p2];z1=np.r_[p1,p3]
   tex=[];pat=[];own=[]
   cube=[]
   # Separate edge chart pair exact actual clipped side orientation; source
   # per-corner UV rows retained even where one geom vertex spans charts.
   for half in (0,1):
    for i in range(N):
     j=(i+1)%N
     ka,kb=int(ids[i]),int(ids[j]);s=lookup_clipped[(kb,ka)]
     a,b=s[1],s[0]
     t=np.array([intrinsic[i],intrinsic[i+1]])
     seam_uv=b-a
     # One exterior transverse rail in the same chart, own face-based
     # 90-degree transverse direction avoids averaging multi-chart corners.
     shift=np.array([seam_uv[1],-seam_uv[0]])*width/leng[i]
     tex.append([a,b,b+shift] if half==0 else [a,b+shift,a+shift])
     pat.append([[t[0],0],[t[1],0],[t[1],width]] if half==0 else [[t[0],0],[t[1],width],[t[0],width]])
     own.append(s[2])
     assert np.array_equal(tex[-1][0],a)
   fuv=np.array(tex,np.float32);fpat=np.array(pat)
   p0b=fpat[:,1]-fpat[:,0];p1b=fpat[:,2]-fpat[:,0];pnorm=p0b[:,0]*p1b[:,1]-p0b[:,1]*p1b[:,0]
   assert (pnorm>0).all()
   def make(M,V):
    M.from_pydata(V.tolist(),[],f.tolist());M.update()
    for nm in skin.data.materials:M.materials.append(nm)
    uv=M.uv_layers.new(name='SameSourceSeamCorners')
    uv.data.foreach_set('uv',fuv.ravel())
    return vec(M.vertices,'co',3).astype(float)
   bind=make(bpy.data.meshes.new(f'{side}.{k}.neutral'),z0);open0=make(bpy.data.meshes.new(f'{side}.{k}.open'),z1)
   def bx(V):return np.cross(V[f[:,1]]-V[f[:,0]],V[f[:,2]]-V[f[:,0]])
   no=bx(open0)
   bo=bx(bind)@(ro@rb.T).T
   den=(bo*bo).sum(1)
   ra=(bo*no).sum(1)/np.maximum(den,1e-30)
   pat_live=make_bvh(open0,f)
   toolpairs=pat_live.overlap(BT)
   joined=pat_live.overlap(body)
   # Shared exact seam points can be in collision list by triangle BVH
   # tangent semantics. Only allow exact source clipped owner and true
   # directly incident same original seam edge from any chart.
   original_ids={v0:set(x for x in upstream[v0] if x>=len(P)) for u0,v0 in joined}
   nonincident=0
   for u0,v0 in joined:
    seam={int(ids[x]) for x in f[u0] if x<L}
    if not seam.intersection(original_ids[v0]):nonincident+=1
   selfp=sum(1 for i,j in pat_live.overlap(pat_live) if i<j and not np.isin(f[i],f[j]).any())
   all_edges=f[:,[0,1,1,2,2,0]].reshape(-1,2)
   ee=np.unique(np.sort(all_edges,axis=1),axis=0)
   edge=lambda V:np.linalg.norm(V[ee[:,1]]-V[ee[:,0]],axis=1)
   qratio=edge(open0)/np.maximum(edge(bind),1e-18)
   # source chart corner preservation checked per oriented edge, no averaging
   # of UV ids across any of the donor multiple-coordinate seam rows.
   old_uv0=np.asarray([lookup_clipped[(int(ids[(i+1)%L]),int(ids[i]))][1] for i in range(L)])
   old_uv1=np.asarray([lookup_clipped[(int(ids[(i+1)%L]),int(ids[i]))][0] for i in range(L)])
   assert np.array_equal(fuv[:L,0],old_uv0.astype(np.float32)) and np.array_equal(fuv[:L,1],old_uv1.astype(np.float32))
   mult_uv=int((np.linalg.norm(np.roll(old_uv1,1,axis=0)-old_uv0,axis=1)>1e-5).sum())
   # ±2mm translated contact truth check downstream coordinates unchanged.
   key=f'{side}_{k}'
   info.append({'branch':k,'paired_edges':L,'faces':len(f),'intrinsic_all_positive':True,'signed_area_fail':int(((ra<.5)|(ra>2)).sum()),
    'edge_guard_fail':int(((qratio<.5)|(qratio>2.)).sum()),'chart_split_vertices_matched':mult_uv,'exact_near_uv_corner_rows':2*L,'reversals':int((ra<=0).sum()),'tool_pairs':len(toolpairs),'retained_nonseam_pairs':nonincident,
    'self_nonadjacent_pairs':selfp,'corridor_length_mm':1000*width,
    'attached_bind_seam_max_um':float(1e6*np.linalg.norm(bind[:L]-p0,axis=1).max()),
    'attached_open_seam_max_um':float(1e6*np.linalg.norm(open0[:L]-p1,axis=1).max())})
   for nm,v in [('bind',bind),('open',open0),('indices',f),('uv',fuv),('intrinsic',fpat),('clipped_source_face_per_triangle',own),('authority_seam_ids',ids)]:
    geom[key+'_'+nm]=np.asarray(v)
   allpan.append((key,pat_live));sidel.append(open0)
  cf=fixture[side+'_compatible_shaft_face'];bar=fixture[side+'_barycentric'];bearing=bar@cf
  t=(bearing-cf[0])@n
  assert float(abs(t).max())<1e-10
  born=.5*np.linalg.norm(np.cross(bearing[1]-bearing[0],bearing[2]-bearing[0]))
  result['hands'][side]={'panels':info,'unchanged_bearing_target_area_mm2':1e6*float(born),
   'negative_true_plane_embedded_mm':float(1000*((bearing-.002*n-cf[0])@n).min()),
   'negative_true_plane_gapped_mm':float(1000*((bearing+.002*n-cf[0])@n).min())}
  geom[side+'_exact_bearing_target']=bearing
 # No raw nearest assign for left web. Pattern landmark perimeter authoring
 # is anatomical by pose transforms rather than source edge projection.
 WF=np.array([[0,1,3],[1,2,3]])
 master=np.r_[web_b,web_o]
 web2=np.array([[0.,0.],[.023,.016],[.053,.025],[.030,-.011]])
 mesh=bpy.data.meshes.new('ExactLeftAnatomicWeb-Section')
 mesh.from_pydata(web_o.tolist(),[],WF.tolist());mesh.update()
 wn=vec(mesh.vertices,'co',3).astype(float)
 rr=np.linalg.norm(np.cross(wn[WF[:,1]]-wn[WF[:,0]],wn[WF[:,2]]-wn[WF[:,0]]),axis=1)
 webtest=make_bvh(wn,WF)
 result['actual_left_web_anatomical_section']={'stable_roles':['thumb proximal crease','thumb/index web ridge','index proximal crease','thenar web return'],
  'triangle_areas_mm2':(5e5*rr).tolist(),'tool_pairs':len(webtest.overlap(BT)),
  'all_original_mesh_pairs':len(webtest.overlap(body)),'complete_new_guard_web_material_binding':False}
 geom.update(left_web_intrinsic_anchors=web2,left_web_bind_anchors=web_b,left_web_open_anchors=wn,left_web_indices=WF)
 inter={}
 for i,(name,A0) in enumerate(allpan):
  for name2,B0 in allpan[i+1:]:
   inter[name+'/'+name2]=len(A0.overlap(B0))
 result['branch_to_branch_pairs']=inter
 result['web_to_cuff_rail_pairs']={name:len(B0.overlap(webtest)) for name,B0 in allpan}
 # Native BVH ignores purely coplanar twin sheets; a genuinely piercing
 # witness is the relevant validated negative, not a coincident triangle.
 qp=geom['R_0_open'][geom['R_0_indices']]
 na=np.cross(qp[:,1]-qp[:,0],qp[:,2]-qp[:,0])
 j0=int(np.linalg.norm(na,axis=1).argmax());q=qp[j0].mean(0);nv=unit(na[j0]);t0=unit(qp[j0,1]-qp[j0,0])
 bad=np.stack([q-.001*nv-.0001*t0,q+.001*nv-.0001*t0,q+.0001*t0])
 test=make_bvh(bad,np.array([[0,1,2]]))
 result['negative_piercing_corridor_pairs']=len(allpan[0][1].overlap(test))
 assert result['negative_piercing_corridor_pairs']>0
 # Zero-collision narrow cuff proof and anatomic section are inputs only.
 # Refuse a full assembly if the branch volumes, tool, or material needs fail.
 result['joined_new_glove_executed']=False;result['closed_or_animated']=False
 np.savez_compressed(p/'editable_intrinsic_panels.npz',**geom)
 (p/'result.json').write_text(json.dumps(result,indent=2,default=lambda a:a.item())+'\n');print(json.dumps(result,indent=2,default=lambda a:a.item()),flush=True)
