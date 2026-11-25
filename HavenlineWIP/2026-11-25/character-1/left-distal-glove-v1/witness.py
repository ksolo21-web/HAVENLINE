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
 panels=Path(os.environ['C1_INTRINSIC_PANELS'])
 assert sha(panels)=='6d9aae39e114ba17d0a30801293278e95a0bd9a4ec0126bbec1a9d2e366575d0'
 p0=np.load(panels)
 seam=Path(os.environ['C1_STITCHED_CUFF_DATA'])
 assert sha(seam/'editable_splice.npz')=='5814ad91f1757e9e4622f8f58999c62aef72267dc63152bf43d67985c556f886'
 assert sha(seam/'result.json')=='f284a3b50abbfa8d8f40b9206e5e18ff0e91b4ce158a7f9a934438271dabff7a'
 js=np.load(seam/'editable_splice.npz')
 fs=json.loads((seam/'result.json').read_text())
 # Retain all exact original source right geometry. Clip and replace L only.
 original=poses()
 keep=np.ones(len(F),bool)
 ee,aa,ww,rr,loops0,cross,far,K,C,Kloc,up=ring['L']
 _,common,labels=donor['L']
 drop=lambda z:z[(labels[weld[F[z]]]==common).all(1)]
 keep[np.r_[drop(cross),drop(far)]]=False
 cloth=js['clipped_source_faces']; i0=len(cloth)//2
 nR=fs['hands']['R']['clipped_retained_source_faces']
 # All R cut nodes precede L nodes under pinned author order. Select left
 # topology using exact distinctive original x; no deletion of right.
 vb=np.r_[P,js['new_bind']];op=np.r_[original,js['new_open']]
 lc=vb[cloth,0].min(1)>.30
 leftclip=cloth[lc]; leftclipUV=js['clipped_source_corner_uv'][lc]
 assert len(leftclip)>fs['hands']['L']['clipped_retained_source_faces']
 # Appended cloth rail IDs reference original pin provenance for near rows;
 # far rows unique and shared with distal panels, exact across both states.
 Vb=vb.tolist();Vo=op.tolist();FN=[];UVs=[];roles=[]; added={}
 for j in (0,1):
  key=f'L_{j}_'; bf0=p0[key+'bind']; of0=p0[key+'open']; N=len(bf0)//2
  ids=p0[key+'authority_seam_ids'].tolist()
  assert np.array_equal(op[ids],of0[:N]) and np.max(np.linalg.norm(vb[ids]-bf0[:N],axis=1))<1e-7
  farrow=list(range(len(Vb),len(Vb)+N)); Vb.extend(bf0[N:].tolist());Vo.extend(of0[N:].tolist())
  rows=np.array(ids+farrow)
  fr=rows[p0[key+'indices']]
  FN.extend(fr.tolist()); UVs.extend(p0[key+'uv'].tolist()); roles+=['L'+str(j)+'_authored_near_rail']*len(fr)
  added[j]=(farrow, bf0, of0, p0[key+'uv'])
 U,Q,H,_,_,_,_,hr,pi,ref,no,ix=sets['L']; Rb=np.array(H.bone.matrix_local);Ro=np.array(H.matrix)
 rb=Rb[:3,:3];ro=Ro[:3,:3]
 local=lambda a,R:(np.asarray(a)-R[:3,3])@R[:3,:3]
 pose=lambda a,R:np.asarray(a)@R[:3,:3].T+R[:3,3]
 rail0,b0,o0,uv0=added[0];rail1,b1,o1,uv1=added[1]
 N=len(rail0)
 raw=local(o0[N:],Ro)
 rawbind=local(b0[N:],Rb)
 cc=raw[:,[0,2]].mean(0)
 ang=np.arctan2(raw[:,2]-cc[1],raw[:,0]-cc[0]);angles=np.unwrap(ang)
 dsgn=1 if angles[-1]>angles[0] else -1
 assert abs(angles[-1]-angles[0])>5
 c=0.5*(local(p0['left_web_open_anchors'],Ro)[3]+local(p0['L_exact_bearing_target'],Ro).mean(0))
 # Regions are prescribed around actual fixed left thumb/index and thenar
 # planes in the anatomical hand frame, before constructing triangles.
 Wn=local(p0['left_web_open_anchors'],Ro)
 Pw=local(p0['L_exact_bearing_target'],Ro)
 froot=Wn.mean(0)
 thumb_angle=np.arctan2(froot[2]-cc[1],froot[0]-cc[0])
 target_angle=np.arctan2(Pw[:,2].mean()-cc[1],Pw[:,0].mean()-cc[0])
 def where(a):return int(np.argmax(np.cos(ang-a)))
 thumb_slot=where(thumb_angle)
 palm_slot=where(target_angle)
 assert thumb_slot!=palm_slot
 # New sleeve/body shape is intrinsic panel grid with 519 parallel grain
 # rows; no index collapsing/zipper at circumference. Closed fingertips are
 # small same-cardinality disk rows end in a single shared terminal.
 params=[(.015,.96),(.029,1.),(.046,.99),(.063,.95),(.082,.86),(.104,.74),(.122,.55),(.137,.32),(.147,.13)]
 railR=[rail0]; registry={i:np.asarray(uv0[j,2]) for j,i in enumerate(rail0)}
 registry.update({i:np.asarray(uv1[j,2]) for j,i in enumerate(rail1)})
 def add(VV,VVbind,uv):
  j=len(Vo);Vb.append(np.asarray(VVbind).tolist());Vo.append(np.asarray(VV).tolist());registry[j]=np.asarray(uv);return j
 for u,scale in params:
  rows=[]
  for j,z in enumerate(angles):
   # Interpolate measured cuff section into clean ergonomic shell; distal
   # palm foundation has a concave inside bias and continuity through rest.
   x=cc[0]*max(0.,1-u/.13)+.050*scale*np.cos(z)
   depth=cc[1]*max(0.,1-u/.13)+.030*scale*np.sin(z)-.013*max(np.sin(z),0)*max(0,1-abs((u-.065)/.065))
   q=np.array([x,u,depth])
   m=np.clip(1-(u-.012)/.034,0,1)
   base_open=q+m*(raw[j]-np.r_[cc[0]+.050*np.cos(z),.008,cc[1]+.030*np.sin(z)])
   base_rest=q+m*(rawbind[j]-np.r_[cc[0]+.050*np.cos(z),.008,cc[1]+.030*np.sin(z)])
   rows.append(add(pose(base_open,Ro),pose(base_rest,Rb),registry[rail0[j]]+np.array([0,u*.6])))
  railR.append(rows)
 def face(a,role,uv=None):
  FN.append(list(a));UVs.append([registry[x].tolist() for x in a] if uv is None else uv);roles.append(role)
 # Select an equal-size rectangular 48-edge hole for the independently
 # sewn nested cuff return, and hard disjoint windows for anatomical web and bearing.
 l1=len(rail1)
 assert l1==48
 q1=local(o1[l1:],Ro).mean(0); port=where(np.arctan2(q1[2]-cc[1],q1[0]-cc[0]))
 def sep(i,j):return min((i-j)%N,(j-i)%N)
 # Width 22 + height 2 gives exactly 48 perimeter edges.
 hs=(port-11)%N; hw=22; startrow=0; hh=2
 trow=3; thcols={(thumb_slot+j)%N for j in range(-6,6)}
 prow=max(3,min(6,int(np.abs(np.asarray(params)[:,0]-Pw[:,1].mean()).argmin())))
 pcols={(palm_slot+j)%N for j in range(-5,5)}
 if prow==trow and bool(thcols&pcols):prow+=1
 tcols0=(thumb_slot-6)%N;pcols0=(palm_slot-5)%N
 for row in range(len(railR)-1):
  A0=railR[row];B0=railR[row+1]
  for j in range(N):
   if (row<hh and (j-hs)%N<hw) or (row==trow and j in thcols) or (row==prow and j in pcols):continue
   j1=(j+1)%N
   # Far rails in prior generated triangulation have reverse walk; attach
   # with opposite edge orientation and preserve per-corner UV boundaries.
   vv=[A0[j],A0[j1],B0[j1],B0[j]]
   role='palmar_thenar' if np.sin(ang[j])>0 else 'dorsal'
   face(vv[:3],role);face([vv[0],vv[2],vv[3]],role)
 def rectangle(y,x,w,h):
  return [railR[y][(x+j)%N] for j in range(w)]+[railR[y+j][(x+w)%N] for j in range(h)]+[railR[y+h][(x+w-j)%N] for j in range(w)]+[railR[y+h-j][x%N] for j in range(h)]
 hhrail=rectangle(startrow,hs,hw,hh)
 assert len(hhrail)==len(rail1)
 # Inner strip uses deliberate one-to-one oriented return, no giant zipper.
 for j in range(l1):
  k=(j+1)%l1
  face([rail1[j],rail1[k],hhrail[k]],'nested_intrinsic_return')
  face([rail1[j],hhrail[k],hhrail[j]],'nested_intrinsic_return')
 # Rebind true pressure front and the 4 bone-defined web landmarks to
 # authored continuous patterns; explicitly triangulate section windows.
 start_open=p0['left_web_open_anchors']; start_bind=p0['left_web_bind_anchors']
 wr=rectangle(trow,tcols0,len(thcols),1);pr=rectangle(prow,pcols0,len(pcols),1)
 tw=[add(x,y,registry[wr[0]]) for x,y in zip(start_open,start_bind)]
 bp=p0['L_exact_bearing_target']
 bearing=[add(x,pose(local(x,Ro),Rb),registry[pr[0]]) for x in bp]
 # Patch backing is not an append: window sides and internal faces share
 # every edge with the surrounding left exterior. Assign specific 2D sector
 # fan to each straight boundary segment, not radial cuff zipper.
 def bridge_window(ex,inner,role):
  nn=len(inner); sz=len(ex);g=np.array_split(np.arange(sz),nn)
  for d,jj in enumerate(g):
   for l in jj:
    q=(l+1)%sz;face([ex[l],ex[q],inner[d]],role)
   q=(jj[-1]+1)%sz;face([ex[q],inner[(d+1)%nn],inner[d]],role)
 bridge_window(wr,tw,'thumb_web_border')
 # Corner order set by preauthored named anatomical landmark sequence.
 face([tw[0],tw[1],tw[3]],'anatomical_web')
 # Add real independent tapered thumb surface with its web attached as a
 # continued sewn panel, rather than leaving the thumb as a flat patch.
 thumbhead=np.array(rig.pose.bones['thumb.02.L'].head)
 tip=.64*thumbhead+.36*start_open[1]+.009*no
 tb=add(tip,pose(local(tip,Ro),Rb),registry[tw[2]])
 face([tw[1],tw[2],tb],'thumb_shell')
 face([tw[2],tw[3],tb],'thumb_shell')
 face([tw[3],tw[1],tb],'thumb_shell')
 bridge_window(pr,bearing,'thenar_pressure_rail')
 bearingId=len(FN);face(bearing,'exact_left_bearing')
 tip=[0,.149,0];tf=add(pose(tip,Ro),pose(tip,Rb),registry[railR[-1][0]])
 for i in range(N):face([railR[-1][i],railR[-1][(i+1)%N],tf],'distal_closed_edge_open_hand')
 V=np.asarray(Vo);B=np.asarray(Vb);new=np.asarray(FN,int)
 full=np.concatenate((F[keep],leftclip,new))
 UV=uvs=np.asarray(UVs,np.float32)
 assert np.array_equal(V[:len(P)],original)
 newoffset=len(full)-len(new)
 # Validate merged held mesh native. Preserve exact original material.
 held=bpy.data.meshes.new('LEFT-only-joined-open')
 held.from_pydata(V.tolist(),[],full.tolist());held.update()
 sm=skin.data
 for m0 in sm.materials:held.materials.append(m0)
 suv=np.zeros((len(sm.uv_layers.active.data),2),np.float32);sm.uv_layers.active.data.foreach_get('uv',suv.ravel())
 fu=suv[vec(sm.loop_triangles,'loops',3,np.int32)]
 uax=np.concatenate((fu[keep],leftclipUV.astype(np.float32),UV))
 ua=held.uv_layers.new(name=sm.uv_layers.active.name);ua.data.foreach_set('uv',uax.ravel())
 assert np.array_equal(uax[:int(keep.sum())],fu[keep])
 VV=vec(held.vertices,'co',3).astype(float)
 tool=make_bvh(TP,T);body=make_bvh(VV,full);newbv=make_bvh(VV,new)
 hits=body.overlap(tool)
 # Whole character measurement ignores unchanged right for left acceptance,
 # but records that negative explicitly rather than erasing it.
 leftA=(B[full,0]>.29).any(1)
 retainedL=[(i,j) for i,j in hits if i<newoffset and leftA[i]]
 leftnew=[(i,j) for i,j in hits if i>=newoffset]
 all_nonadj=set()
 welded=np.r_[weld,np.arange(weld.max()+1,weld.max()+1+len(V)-len(P))]
 for i,j in newbv.overlap(body):
  if i+newoffset!=j and not np.isin(welded[new[i]],welded[full[j]]).any():
   all_nonadj.add(tuple(sorted((i+newoffset,j))))
 uc=np.sort(np.concatenate([full[:,[0,1]],full[:,[1,2]],full[:,[2,0]]]),axis=1)
 e,cnt=np.unique(uc,axis=0,return_counts=True)
 edge_counts={tuple(a):int(c) for a,c in zip(e,cnt) if a[0]>=len(P)}
 def shape_area(V,F):return np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]])
 normals=shape_area(B,new)@(ro@rb.T).T
 n1=shape_area(VV,new);den=(normals*normals).sum(1)
 signed=(normals*n1).sum(1)/np.maximum(den,1e-22)
 en=np.unique(np.sort(np.concatenate([new[:,[0,1]],new[:,[1,2]],new[:,[2,0]]]),axis=1),axis=0)
 ed=lambda V:np.linalg.norm(V[en[:,0]]-V[en[:,1]],axis=1)
 er=ed(VV)/np.maximum(ed(B),1e-12)
 fa=TP[T[constraints['L']['surface_face_index']]]
 sp=(VV[new[bearingId]]-fa[0])@no
 webids=np.array(tw)
 out={'status':'HOLD_OPEN_IF_ANY_WHOLE_GATE_FAILS','native_join_same_leftcuff_and_axe':True,
 'exact_right_original_unchanged':bool(keep[(P[F,0]<-.29).any(1)].all()),
 'exact_original_retained_uv':True,'original_faces_retained':int(keep.sum()),'new_faces':len(new),
 'part_locally_guarded_edges_bad':int(((er<.5)|(er>2.)).sum()),'signed_faces_bad':int(((signed<.5)|(signed>2.)).sum()),'reversed_or_unoriented':int((signed<=0).sum()),
 'whole_character_all_axe_triangle_pairs':len(hits),'unchanged_other_side_pairs':len(hits)-len(retainedL)-len(leftnew),
 'retained_left_forearm_or_shell_pairs':len(retainedL),'left_new_tool_pairs':len(leftnew),'left_new_off_band_pairs':sum(j not in ix for i,j in leftnew),
 'left_new_unassigned_exact_face_pairs':sum(j!=constraints['L']['surface_face_index'] for i,j in leftnew),
 'new_nonadjacent_whole_pairs':len(all_nonadj),'new_bad_incidences':sum(edge_counts.get(tuple(v),0)!=2 for v in en),
 'actual_attached_bearing_area_mm2':float(5e5*np.linalg.norm(n1[bearingId])),
 'actual_attached_signed_bearing_um':(1e6*sp).tolist(),
 'left_web_4_open_landmark_residual_um':float(1e6*np.linalg.norm(VV[webids]-start_open,axis=1).max()),
 'source_material_web_133_edge_transfer_validated':False,'closure':False}
 from collections import Counter
 out['role_signed_fails']=dict(Counter(roles[k] for k in np.flatnonzero((signed<.5)|(signed>2.))))
 out['off_band_by_role']=dict(Counter(roles[i-newoffset] for i,j in leftnew if j not in ix))
 # Exact role breakdown for potential source-authoring remediation.
 rolekey=lambda j: roles[j-newoffset] if j>=newoffset else ('retained_left' if leftA[j] else 'retained_other')
 out['nonadjacent_joint_by_role']=dict(Counter('/'.join(sorted((rolekey(i),rolekey(j)))) for i,j in all_nonadj))
 # Chart split authority is carried at the paired near seams. Far generator
 # assigned one palette value to each connected vertex; matching adjacency
 # must be independently checked, not implied by original retained UV.
 farUvs={}
 for face0,u0 in zip(new[:2*(len(rail0)+len(rail1))],UV[:2*(len(rail0)+len(rail1))]):
  for q,c0 in zip(face0,u0):farUvs.setdefault(int(q),[]).append(c0)
 out['far_rail_multichart_vertices_not_production_bound']=sum(bool(np.linalg.norm(np.array(farUvs[i])-farUvs[i][0],axis=1).max()>1e-5) for i in rail0+rail1)
 out['negative_assigned_face_embedded_2mm']=float(1000*((VV[new[bearingId]]-.002*no-fa[0])@no).min())
 out['negative_assigned_face_gapped_2mm']=float(1000*((VV[new[bearingId]]+.002*no-fa[0])@no).min())
 np.savez_compressed(p/'editable_left_join.npz',bind_additions=B[len(P):],open_additions=VV[len(P):],new_faces=new,retained_source_faces=np.flatnonzero(keep),
  clipped_left_source_faces=leftclip,clipped_left_corner_uv=leftclipUV,new_corner_uv=UV,roles=np.asarray(roles),left_outer_far_rail=rail0,left_nested_far_rail=rail1,
  true_bearing_face=new[bearingId],web_landmark_ids=webids)
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda x:x.item())+'\n');print(json.dumps(out,indent=2,default=lambda x:x.item()),flush=True)
