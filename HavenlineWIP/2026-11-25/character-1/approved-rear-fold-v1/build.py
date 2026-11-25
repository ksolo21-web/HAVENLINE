import os
import bpy,numpy as np,hashlib,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
P=Path(__file__).resolve().parent
S=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
A=Path(os.environ['C1_COLLAR_DATA'])
N=Path(os.environ['C1_ANTERIOR_BIND_DATA'])
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'exact-assembled-surface.npz')=='8a7222ecdb893da3da09dba34ac3c56f1f95f7f6e7269f1e9d165eca0ef074f7'
assert h(N/'exact-native-witness.npz')=='ba342c9741f7a6a37fbd7acfe7507063dcecdd89137ae045176c0cdb1335d838'
assert h(N/'c1-right-anterior-seam-binding-proof.blend')=='3bee70b2e6248aa7409e9956f13e36684056eb6f93413de94438fff909a10933'
assert h(S)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
a=np.load(A/'exact-assembled-surface.npz'); hw=np.load(N/'exact-native-witness.npz');d=np.load(S)
V=a['v'];T=a['tri'];uv=a['UV'].reshape(len(T),3,2);W=a['w'].copy()
assert np.array_equal(hw['v'],V) and np.array_equal(hw['tri'],T)
W[hw['i']]=hw['new']; assert hw['i'].tolist()==[13484,13613,14018,14078]
x,y,z=V.T
roi=(x>-.165)&(x<-.066)&(y>.058)&(z>.361)&(z<.495)&(W[:,2:].sum(1)<1e-9)
cut=roi[T].all(1);orig=T[cut];oi=np.flatnonzero(cut)
assert cut[[38082,39703]].all() and not roi[hw['i']].any()
def loop(t):
 e={}
 for f in t:
  for i,j in zip(f,np.roll(f,-1)):
   i=int(i);j=int(j)
   if (j,i) in e:del e[j,i]
   else:e[i,j]=1
 rim={i:j for i,j in e}; assert len(rim)==len(e)
 s=[min(rim)]
 while len(s)<len(rim):
  n=rim[s[-1]];assert n not in s;s.append(n)
 assert rim[s[-1]]==s[0]
 return s,e
rim,old_edge=loop(orig);nr=len(rim)
P2=V[rim][:,[0,2]]; S2=V[orig][:,:,[0,2]]
def donor(uv):
 A=S2[:,0];b=S2[:,1]-A;c=S2[:,2]-A;y=uv-A
 det=b[:,0]*c[:,1]-b[:,1]*c[:,0]
 j=(y[:,0]*c[:,1]-y[:,1]*c[:,0])/det
 k=(b[:,0]*y[:,1]-b[:,1]*y[:,0])/det
 p=np.stack((1-j-k,j,k),1)
 pick=int(np.argmax(p.min(1)));return pick,p[pick]
def clearance(v,P):
 d=np.roll(P,-1,axis=0)-P;q=v-P
 u=np.clip((q*d).sum(1)/(d*d).sum(1),0,1)
 return np.linalg.norm(q-u[:,None]*d,axis=1).min()
# Explicit horizontal flex/stitch corridor around measured knee. Middle
# rows placed independently from old dent/fold locations.
Xn=np.linspace(-.155,-.073,8); Zn=np.array([.369,.386,.402,.418,.431,.444,.457,.472,.487])
vertices=P2.tolist(); connectors=[(i,(i+1)%nr) for i in range(nr)]
# Measured max-Y envelope edge carriers impose owner's protected side
# outline as explicit additional constrained seams. No further shape guessing.
def edges_of(t):
 f=np.sort(t[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1)
 return np.unique(f,axis=0)
Eall=edges_of(T); regionEdges={tuple(p.tolist()) for p in edges_of(orig)}
E=V[Eall]; low=E[:,:,2].min(1);hi=E[:,:,2].max(1)
act=set()
for zz in np.linspace(.356,.501,2001):
 ids=np.flatnonzero((low<=zz)&(hi>=zz)&(hi>low)); val=E[ids]
 vv=(zz-val[:,0,2])/(val[:,1,2]-val[:,0,2]);y=(1-vv)*val[:,0,1]+vv*val[:,1,1]
 ix=ids[y.argmax()]; K=tuple(Eall[ix].tolist())
 if K in regionEdges:act.add(K)
carriers=sorted(act); protect={r:i for i,r in enumerate(rim)}; svCarrier=set()
for a0,b0 in carriers:
 for vi in (a0,b0):
  if vi not in protect:
   protect[vi]=len(vertices); vertices.append(V[vi,[0,2]].tolist())
 connectors.append((protect[a0],protect[b0]))
 svCarrier.add(tuple(sorted((protect[a0],protect[b0]))))
carrier2=V[np.asarray(carriers)][:,:,[0,2]]
carrier_gap=lambda p: np.min(np.linalg.norm(carrier2[:,0]+np.clip(((p-carrier2[:,0])*(carrier2[:,1]-carrier2[:,0])).sum(1)/((carrier2[:,1]-carrier2[:,0])**2).sum(1),0,1)[:,None]*(carrier2[:,1]-carrier2[:,0])-p,axis=1))

extra=[]
for hh in Zn:
 last=None
 for xx in Xn:
  p=np.array([xx,hh]);j,w=donor(p)
  if w.min()<-1e-7 or min(clearance(p,P2),carrier_gap(p))<.003: last=None;continue
  i=len(vertices);vertices.append(p.tolist());extra.append(p.tolist())
  if last!=None and donor((p+np.asarray(vertices[last]))*.5)[1].min()>=-1e-8:pass # avoid crossing exact added outline carriers
  last=i
rt=delaunay_2d_cdt([Vector(v) for v in vertices],connectors,[list(range(nr))],1,1e-10)
Q,ed,tri,origv,orige,origf=rt
Q=np.array([q[:] for q in Q],np.float64)
keep2={ix:rv for rv,ix in protect.items()}
rim_to_new={}
for j,idx in enumerate(origv):
 for i in idx:
  if i<nr:
   assert i not in rim_to_new
   rim_to_new[i]=j
assert len(rim_to_new)==nr
rev={j:rim[i] for i,j in rim_to_new.items()}
for j,ss in enumerate(origv):
 true=[keep2[i] for i in ss if i in keep2]
 assert len(true)<=1
 if true:rev[j]=true[0]
live_faces=np.array(tri,int);assert len(live_faces)>0 and live_faces.shape[1]==3
bpy.ops.wm.open_mainfile(filepath=str(N/'c1-right-anterior-seam-binding-proof.blend'))
old=bpy.data.objects['Right boot visible repaired leather rest proof'];arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
oldNormals=np.array([v.vector[:] for v in old.data.corner_normals]).reshape(len(T),3,3)
def sm(t):t=np.clip(t,0,1);return t*t*(3-2*t)
xyz=V.tolist(); ww=W.tolist(); fresh=[]; donor_idx=[]
knee=float(d['joints'][1,1,2])
for j,p in enumerate(Q):
 if j in rev:continue
 t,bs=donor(p)
 assert bs.min()>-1e-5,(p,bs)
 oldp=bs@V[orig[t]]
 # Real visible recess toward front in newly sewn posterior cloth only.
 # Shallow rest slack opening is continuous into exact preserved boundary.
 radial=np.clip(min(clearance(p,P2),carrier_gap(p))/.021,0,1);shape=sm(radial)
 fwd=.012*shape*np.exp(-((p[1]-knee)/.045)**2)
 new=oldp.copy();new[1]-=fwd
 # broad but finite Thigh/Shin material corridor in newly authored rows;
 # exact unchanged bone primitives and all live old rim groups.
 up=sm((p[1]-(knee-.049))/.103)
 w0=bs@W[orig[t]];w0=(1-shape)*w0+shape*np.array([up,1-up,0,0])
 w0=np.fmax(w0,0);w0/=w0.sum()
 rev[j]=len(xyz)
 xyz.append(new.tolist());ww.append(w0.tolist());fresh.append([float(fwd),float(p[1]),int(oi[t])]);donor_idx.append(int(oi[t]))
X=np.asarray(xyz);RW=np.asarray(ww)
F=[];UV=[];NL=[];MIX=0
for ft in live_faces:
 g=[rev[k] for k in ft]; aa=X[g]
 if np.cross(aa[1]-aa[0],aa[2]-aa[0])[1]<0:g=g[::-1]
 F.append(g)
 # Preserve source projection with explicit atlas-chart registration:
 # closest surface is never used to choose geometry; for UVs, use same containing
 # measured source chart and respect intentional discontinuities.
 so,bc=donor(X[g].mean(0)[[0,2]])
 chart=uv[oi[so]]
 cu=[];cn=[]
 for j in g:
  k,b=donor(X[j][[0,2]])
  tu=b@uv[oi[k]]
  # At a cross-atlas seam keep this new loop attached to its chosen face
  # donor instead of stretching across unrelated texture islands.
  if np.linalg.norm(tu-chart.mean(0))>.075:
   MIX+=1
   p=X[j][[0,2]]; q=V[orig[so]][:,[0,2]];a=q[0];bxy=(q[1:]-a).T
   v0=np.linalg.solve(bxy,p-a);mul=np.r_[1-v0.sum(),v0];mul=np.maximum(mul,0);mul/=mul.sum()
   tu=mul@chart
  cu.append(tu)
  normal=b@oldNormals[oi[k]];normal/=np.linalg.norm(normal);cn.append(normal)
 UV.append(cu);NL.append(cn)
F=np.array(F)
assert loop(F)[1]==old_edge, 'new panel seam topology differs'
allT=np.vstack((T[~cut],F));provenance=np.r_[np.flatnonzero(~cut),np.full(len(F),-1)]
alluv=np.concatenate((uv[~cut],np.array(UV)));ns=np.concatenate((oldNormals[~cut],np.array(NL)))
objmesh=bpy.data.meshes.new('Single retopologized visible rear-knee slack panel')
S0=float(d['scale']); O=d['source_origin']
objmesh.from_pydata((X/S0+O).tolist(),[],allT.tolist());objmesh.update()
o=bpy.data.objects.new('Right boot new visible rear fold candidate',objmesh);bpy.context.collection.objects.link(o)
ll=objmesh.uv_layers.new(name='Source registered posterior fabric atlas');ll.data.foreach_set('uv',alluv.astype(np.float32).ravel())
for f in objmesh.polygons:f.use_smooth=True
objmesh.normals_split_custom_set(ns.reshape(-1,3).tolist());objmesh.materials.append(old.data.materials[0])
gs=[o.vertex_groups.new(name=k) for k in ('thigh.R','shin.R','foot.R','toe.R')]
for i,row in enumerate(RW):
 for g,w in zip(gs,row):
  if w>1e-10:g.add([i],float(w),'REPLACE')
m=o.modifiers.new('Exact C1 articulation','ARMATURE');m.object=arm
old.hide_set(True);old.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-visible-rear-knee-redesign-proof.blend'),compress=True)
np.savez_compressed(P/'new-rear-panel.npz',v=X,tri=allT,w=RW,u=alluv,region=np.arange(len(T)-int(cut.sum()),len(allT)),old_kept=provenance,cut_ids=oi,boundary=np.array(rim))
out={'authored_panel_triangles':len(F),'removed_old_posterior_triangles':len(orig),'exact_sewn_boundary_rows':nr,'new_visible_rows':len(fresh),'material_loops_with_local_chart_clamp':MIX,'back_indent_max_mm':max(f[0] for f in fresh)*1000,'excluded_exact_anterior_vertices':hw['i'].tolist(),'outline_carrier_edges':carriers}
(P/'build.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
