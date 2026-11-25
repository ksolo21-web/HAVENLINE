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
 base=poses(); BT=make_bvh(TP,T)
 parent=Path(os.environ['C1_GLOVE_PANEL_RESULT'])
 assert sha(parent)=='e395caf61510aaba8b36e41373325072cab0c0d14704e02f370b9aa3063bb175'
 old=make_bvh(base,F).overlap(BT); assert len(old)==370
 raw_direct=np.unique([i for i,j in old])
 # Full incident faces from a 24mm circumferential rest-domain shell around
 # the exact palm/forearm/cuff intersections. All remaining facial corners
 # untouched. Original UV seams remain independent corner data, not welded.
 tree=cKDTree(P[np.unique(F[raw_direct])])
 d=tree.query(P,k=1)[0]
 selected=(d[F].min(1)<.024)&(np.abs(P[F,0]).min(1)>.565)
 sel=np.flatnonzero(selected)
 assert np.isin(raw_direct,sel).all()
 # Require original outer boundary as segment-for-segment with BOTH side
 # vertices locked (position seam groups use exact bind positions).
 pairs=np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],axis=0)
 wpair=np.sort(weld[pairs],axis=1)
 keys,which=np.unique(wpair,axis=0,return_inverse=True)
 inc=np.bincount(which); pc=np.bincount(which,weights=np.tile(selected,3),minlength=len(keys)).astype(int)
 boundary_w=np.unique(keys[(pc>0)&((inc!=pc)|(inc==1))])
 boundary=np.isin(weld,boundary_w)
 sm=skin.data
 olduv=np.empty((len(sm.uv_layers.active.data),2),np.float32)
 sm.uv_layers.active.data.foreach_get('uv',olduv.ravel())
 tri_loops=vec(sm.loop_triangles,'loops',3,np.int32)
 FU=olduv[tri_loops]
 # Full one-owner shape and skin art positions, with one new independent
 # topology fan per old triangle. All internal shape directions come from
 # assigned faceted shaft and separately authorized diagnostic open controls.
 bary_new=np.array([[1.,0.,0.],[0.,1.,0.],[0.,0.,1.],[1/3,1/3,1/3]],float)
 tile=np.array([[0,1,3],[1,2,3],[2,0,3]])
 coeffs=np.zeros((len(P)+len(sel),2),np.float32)
 RN=np.concatenate((P,P[F[sel]].mean(1)))
 ON=np.concatenate((base,base[F[sel]].mean(1)))
 fn=np.concatenate([F[~selected],np.column_stack((F[sel],np.arange(len(P),len(RN))))[:,tile].reshape(-1,3)])
 Uvn=np.concatenate([FU[~selected],np.einsum('tik,ji->tjk',FU[sel],bary_new)[:,tile].reshape(-1,3,2)])
 parent_faces=np.r_[np.flatnonzero(~selected),np.repeat(sel,3)]
 assert len(fn)==len(F)+2*len(sel)
 assert np.array_equal(RN[:len(P)],P)
 # Derived concave interior solid mold by radial shaft facet planes; each
 # side retains positive gap beyond its side hemisphere. Thumb moves
 # independently with an open-rotation local support; cuffs inherit 0 at seam.
 away=ON.copy()
 new_pin=np.r_[boundary,np.zeros(len(sel),bool)]
 localmask=np.zeros(len(RN),bool);localmask[np.unique(fn[len(F)-len(sel):])]=True
 delta=np.zeros_like(ON)
 side_report={}
 for side,(U,Q,H,_,_,_,_,_,pi,ref,n,ix) in sets.items():
  sgn=-1 if side=='R' else 1
  ii=np.flatnonzero(localmask & ~new_pin & (sgn*RN[:,0]>.565))
  sector=np.array([1.,0.,0.])*(-1 if side=='R' else 1)
  pplanes,off=signed_planes(A,T[ix])
  xx=(ON[ii]-factory-dt)@M
  zz=xx[:,2]
  # Cross section profile for in-band palm; rails are anchored at original
  # indexed outline. Shared local wrist/cuff/palm supports only.
  hf,_,_=np.linalg.svd(np.stack([n,unit(M[:,2])]).T,full_matrices=True)
  inband=abs(zz-constraints[side]['grip_center_in_original_axis'])<.045
  positive=np.flatnonzero(pplanes@sector>.2)
  chosen=positive[np.argmax((xx@pplanes.T-off)[:,positive],axis=1)]
  signed=(xx*pplanes[chosen]).sum(1)-off[chosen]
  # outward local mold; can move inward only within selected side and
  # shallow near the bearing area, not toward opposite half or stem.
  palm=(RN[ii,0]*sgn>.70)&inband&((xx@sector)>.026)&(signed<.005)&(signed>-.020)
  shift=np.maximum(.00005-signed,-.00075)
  mold=(pplanes[chosen]@M.T)*shift[:,None]
  # Separate thumb-/wrist-panel controls use original region supports and
  # a physically bounded open relief, independently of the concave cup.
  wt=(W[:,lookup['thumb.01.'+side]]+W[:,lookup['thumb.02.'+side]]+W[:,lookup['thumb.03.'+side]])
  thumb=np.r_[wt,wt[F[sel]].mean(1)][ii]
  fw=W[:,lookup['forearm.'+side]]
  cuff=np.r_[fw,fw[F[sel]].mean(1)][ii]
  eps=np.r_[d,d[F[sel]].mean(1)][ii]
  t=((.024-eps)/.010).clip(0,1);t=t*t*(3-2*t)
  cthumb=(thumb>.22)&(eps<.013)&~palm
  ccuff=(cuff>.2)&(eps<.014)&~palm
  # Separate stored panel-control amplitudes with bind value zero for both.
  coeffs[ii,0]=cthumb*t*.0085
  coeffs[ii,1]=ccuff*t*.0035
  relief=(coeffs[ii,0]+coeffs[ii,1])[:,None]*n
  delta[ii]=mold*palm[:,None]*t[:,None]+relief
  side_report[side]={'mold_vertices':int(palm.sum()),'separate_open_thumb_region':int(cthumb.sum()),'separate_open_cuff_region':int(ccuff.sum())}
 away+=delta
 assert np.array_equal(away[np.flatnonzero(new_pin)],ON[np.flatnonzero(new_pin)])
 # Native meshes made from new indexed topology and exact inherited corner UVs.
 # Use the donor material object unchanged, no visually authored material proxy.
 def diagnostic_native(name,V):
  mesh=bpy.data.meshes.new(name)
  # Material pointer reused verbatim, in-memory only.
  mesh.from_pydata(V.tolist(),[],fn.tolist());mesh.update()
  for material in sm.materials:mesh.materials.append(material)
  uv=mesh.uv_layers.new(name=sm.uv_layers.active.name)
  uv.data.foreach_set('uv',Uvn.astype(np.float32).reshape(-1))
  mesh.update()
  return mesh
 N=diagnostic_native('Exact-Neutral-Topo',RN)
 O=diagnostic_native('Exact-Compact-Open-Topo',away)
 assert len(N.polygons)==len(O.polygons)==len(fn)
 assert [m.name for m in O.materials]==[m.name for m in sm.materials]
 V=vec(O.vertices,'co',3).astype(float)
 assert np.array_equal(V[:len(P)][boundary],base[boundary])
 assert np.array_equal(vec(N.vertices,'co',3)[:len(P)],P)
 # neutral subdivision is the exact original triangular support as all
 # extra cents are barycentric, including outline and neutral UV corners.
 forced=np.linalg.norm(RN[len(P):]-np.einsum('tij,i->tj',P[F[sel]],bary_new[-1]),axis=1).max()
 assert forced<3e-15
 tf=len(F)-len(sel);newfaces=fn[tf:]
 norm=lambda p,f:np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
 N0=norm(ON,newfaces);N1=norm(V,newfaces)
 valid=(N0*N0).sum(1)>1e-24
 ratios=(N1[valid]*N0[valid]).sum(1)/((N0[valid]*N0[valid]).sum(1))
 ar=make_bvh(V,fn)
 hits=ar.overlap(BT)
 patch=make_bvh(V,newfaces)
 fullW=np.r_[weld,np.arange(weld.max()+1,weld.max()+1+len(sel))]
 selfpair=set((min(i+tf,j),max(i+tf,j)) for i,j in patch.overlap(ar) if i+tf!=j and not np.isin(fullW[newfaces[i]],fullW[fn[j]]).any())
 for side,(*_,ix) in sets.items():
  sgn=-1 if side=='R' else 1
  sideids=sgn*RN[fn,0].min(1)>.56 if side=='L' else (-RN[fn,0]).min(1)>.56
  hh=[(i,j) for i,j in hits if sideids[i]]
  cuffsource=W[:,lookup['forearm.'+side]]>.002
  owned=cuffsource[F[parent_faces]].any(1)
  side_report[side].update(tool_pairs=len(hh),offband=sum(j not in ix for i,j in hh),
    forearm_cuff=sum(owned[i] for i,j in hh))
  source_side=np.unique(fn[sideids])
  w0=(V[source_side]-factory-dt)@M
  planes,off=signed_planes(A,T[ix]);z=constraints[side]['grip_center_in_original_axis']
  v0=np.maximum(np.max(w0@planes.T-off,axis=1),abs(w0[:,2]-z)-.05)
  side_report[side]['max_signed_prism_entry_mm']=float(1000*min(0,v0.min()))
  side_report[side]['inside_over_0_2mm']=int((v0<-.0002).sum())
  target=TP[T[constraints[side]['surface_face_index']]]
  n=sets[side][-2]
  dual=np.linalg.pinv((target[1:]-target[0]).T)
  vv=V[newfaces]-target[0]; signed=vv@n; bc=vv@dual.T
  hit=((signed>=0)&(signed<.00015)&(bc.min(2)>=0)&(bc.sum(2)<=1)).all(1)
  side_report[side]['near_plane_triangle_count']=int(hit.sum())
  side_report[side]['near_plane_area_mm2']=float(5e5*np.linalg.norm(N1[hit],axis=1).sum())
 def edges(f):
  return np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0)
 lens=lambda a,e:np.linalg.norm(a[e[:,1]]-a[e[:,0]],axis=1)
 e=edges(newfaces);le=lens(ON,e);good=le>1e-9;rr=lens(V,e)[good]/le[good]
 bind=Path(os.environ['C1_BIND_EVIDENCE'])
 assert sha(bind)=='d44de88c78aec4f98c80d379c549c2a9d2f6d1bf54d5288c150ed1d1f51aa336'
 legacy=np.load(bind)
 assert np.array_equal(legacy['P'],P.astype(np.float32)) and np.array_equal(legacy['F'],F)
 bE=edges(F);ell=lens(P,bE);wi=legacy['W']/1000.;ci=[i for i,n in enumerate(legacy['names']) if n.endswith('.01.L')]
 lm=wi[:,ci].argmax(1);wm=wi[:,ci].max(1);l,r=bE.T
 vv=(X0>.744)&(X0<.850)&(Z0>.387)&(Z0<.503)&(Y0>.028)
 web=vv[l]&vv[r]&(ell>.00045)&(lm[l]!=lm[r])&(wm[l]>.3)&(wm[r]>.3);assert web.sum()==133
 wr=lens(V,bE[web])/ell[web]
 out={'status':'HOLD_TOPOLOGY_NATIVE_OPEN','baseline_pairs':370,'open_pairs':len(hits),'open_unique_parent_tool_pairs':len(set((int(parent_faces[i]),int(j)) for i,j in hits)),'original_vertices':len(P),'new_centroid_vertices':len(sel),
 'edge_fail':int(((rr<.5)|(rr>2.)).sum()),'original_web_133_min':float(wr.min()),'original_web_133_max':float(wr.max()),'original_web_133_fail':int(((wr<.5)|(wr>2.)).sum()),'original_triangles':len(F),'total_triangles':len(fn),'exact_boundary_vertex_rows':int(boundary.sum()),
 'outside_original_faces':len(F)-len(sel),'neutral_barycentric_error_m':float(forced),'topology_guard_areas_under_half_or_over_double':int(((ratios<.5)|(ratios>2.)).sum()),
 'topology_guard_area_reversals':int((ratios<=0).sum()),'open_weld_excluded_nonadjacent_self_pairs':len(selfpair),
 'lower_untouched_exact':bool(np.array_equal(V[:len(P)][fixed],original[fixed])),
 'sides':side_report,'max_open_supported_delta_mm':float(1000*np.linalg.norm(delta,axis=1).max()),'closed_or_animated':False}
 assert out['lower_untouched_exact']
 # Compact editable replacement only; original asset needed for context.
 np.savez_compressed(p/'editable_insert.npz',selected_source_triangles=sel, replacement_indices_global=newfaces,
  center_bind_mm=1000*RN[len(P):],native_open_delta_mm=(1000*delta[localmask]).astype('float32'),
  native_open_delta_global_indices=np.flatnonzero(localmask),corner_uv=Uvn[tf:].astype('float32'),
  centroid_bary=bary_new[-1],per_corner_face_mapping=parent_faces[tf:],thumb_cuff_open_amplitudes=coeffs[localmask])
 (p/'result.json').write_text(json.dumps(out,indent=2,default=lambda v:v.item())+'\n');print(json.dumps(out,indent=2,default=lambda v:v.item()),flush=True)
