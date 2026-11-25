import os
import hashlib,json,numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation,Slerp
P=Path(__file__).resolve().parent
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
A=(Path(os.environ['C1_KNEE_DATA'])/'poses.npz')
assert h(A)=='c16ef2874698851d6a237e14779166f2346ca3d89f4e520738252769664d2ef5'
assert h(Path(os.environ['C1_EXACT_GLB']))=='7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb'
assert h(Path(os.environ['C1_EXACT_BLEND']))=='a540243d96fcc3a8d97eb9c13cf6fc9fc700707e379060d087ae986a346b50df'
d=np.load(A); X=d['rest'].astype(float); F=d['tri'];E=d['E']; org=d['source_origin'];sc=float(d['scale']);Y=d['frames'].astype(float)
_,rep,inv=np.unique(np.rint(X/1e-6).astype('int64'),axis=0,return_index=True,return_inverse=True);U=X[rep]
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def metric(a):return np.linalg.norm(a,axis=-1)
def aff(mat,pts):
 pp=np.array(pts)/sc+org
 return ((pp@mat[:3,:3].T)+mat[:3,3]-org)*sc
def polar_interp(A,B,t):
 return Slerp([0,1],Rotation.from_matrix(np.array([A[:3,:3],B[:3,:3]])))(t).as_matrix()
def cellkeys(rings):
 out=[]
 for i in range(len(rings)-1):
  for j in range(N):
   a=i*N+j; b=i*N+(j+1)%N
   out.append((a,b,b+N,a+N))
 return np.array(out)
def normals(Y,F):
 a=Y[F];return np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0])
N=16; theta=np.linspace(0,2*np.pi,N,endpoint=False)
D=np.stack([np.cos(theta),np.sin(theta)],1)
prod=Y.copy();report={}; meshes=[]; maps={}
for i,s in enumerate('LR'):
 w=d['weights'][:,i*4:i*4+4].sum(1); sgn=1 if s=='L' else -1
 Hip,Knee,Ankle,Toe=d['joints'][i]
 # Independently authored visible-part-neutral interior geometry: lower outsole blocks and toe
 # plates have explicit separation at true ToeBase; boot shaft sewn flex rings bridge to shin.
 zlo=.074; zhi=min(float(Hip[2])+.020,float(np.quantile(X[(w>.85)&(X[:,0]*sgn>.025),2],.995))); levels=np.sort(np.unique(np.r_[np.linspace(zlo,zhi,14),Ankle[2]-.026,Ankle[2]+.01,Ankle[2]+.046,Knee[2]-.033,Knee[2],Knee[2]+.033]))
 levels=levels[(levels>=zlo)&(levels<=zhi)]
 support=(w>.85)&(X[:,0]*sgn>.025)&(X[:,2]>zlo)&(X[:,2]<zhi)
 protected=(X[:,2]<=.075)|(d['weights'][:,i*4+2:i*4+4].sum(1)>.99999)
 protected[d['footprint'+s]]=True
 keep=np.zeros(len(U),bool);keep[inv[(~support)|protected]]=True
 change=np.flatnonzero(~keep)
 # Interior profile from named sections: retain a narrow internal working envelope so
 # no new outward silhouette. Use actual sections, not donor boot dimensions.
 C=[]; rad=[]
 for z in levels:
  mask=(w>.65)&(sgn*X[:,0]>.03)&(abs(X[:,2]-z)<.032)
  if sum(mask)<20: raise RuntimeError((s,z,'section missing'))
  q=X[mask,:2];lo,hi=np.quantile(q,[.15,.85],axis=0)
  C.append(np.r_[.5*(lo+hi),z])
  rad.append(np.maximum(.011,.26*(hi-lo)))
 C=np.asarray(C);rad=np.asarray(rad)
 ring=(C[:,None,:2]+D[None]*rad[:,None]);v=np.c_[ring.reshape(-1,2),np.repeat(levels,N)]
 f=cellkeys(levels)
 meshes.append((s,'shaft_flex_rings',v,f))
 # Polygonal insole/toe hinge prototype occupies material interior; editable geometry
 # not tied to old visible vertex topology. Independent limb rest foot center is fixed.
 topz=max(.037,min(.054,Toe[2]*.24))
 toe_x=Toe[0];toe_y=Toe[1]
 for name,y0,y1 in [('rear_rigid_plate',toe_y+.010,Ankle[1]+.045),('toe_rocker_plate',toe_y-.078,toe_y-.010)]:
  pp=np.array([[toe_x+a,y,z] for z in (.028,topz) for y,a in [(y0,-.027),(y0,.027),(y1,.027),(y1,-.027)]])
  meshes.append((s,name,pp,np.array([(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])))
 ii=np.searchsorted(levels,U[change,2],side='right')-1;ii=np.clip(ii,0,len(levels)-2)
 zz=(U[change,2]-levels[ii])/(levels[ii+1]-levels[ii])
 cr=(1-zz[:,None])*C[ii]+zz[:,None]*C[ii+1]
 offsets=U[change]-cr
 scope=np.flatnonzero(np.isin(inv,change))
 take=np.searchsorted(change,inv[scope])
 z=U[change,2]
 # Every visible material vertex follows the newly authored interior sectional
 # frame, with stock unchanged at ankle outsole and proximal join. Residual is
 # stored exactly at rest, so original PBR, silhouette, UV and geometry not remeshed.
 smooth_boundary=smooth((z-zlo)/.030)*smooth((zhi-z)/.032)
 mapped0=cr+offsets
 assert np.max(metric(mapped0-U[change]))<1e-12
 T0=normals(X,F)
 faces=np.flatnonzero(np.isin(inv[F],change).any(1))
 case=[]
 for key,(orig,mats) in enumerate(zip(Y,d['bones'][:,i])):
  ringrot=[];cent=[]
  for A0 in C:
   z=A0[2];a=float(Ankle[2]);k=float(Knee[2])
   if z<k-.063:
    blend=smooth((z-(a-.040))/.102); m,n=mats[2],mats[1];w0=blend
   elif z>k+.063:
    m,n=mats[0],mats[0];w0=0.
   else:
    blend=smooth((z-(k-.063))/.126); m,n=mats[1],mats[0];w0=blend
   ringrot.append(polar_interp(m,n,w0))
   cent.append((1-w0)*aff(m,A0)+w0*aff(n,A0))
  cent=np.asarray(cent); ringrot=np.asarray(ringrot)
  # Actual separate ring scaffold posing only; proper frames and forward
  # centerline retained; no claim of global nonintersection/inversion.
  ring_disp=np.einsum('nij,nkj->nki',ringrot,v.reshape(-1,N,3)-C[:,None])+cent[:,None]
  # Continuous ruled shell mapping over adjacent flex rings, with source sub-facet
  # offset carried by the ring frame. Independent plate surfaces don't affect sole.
  rg0=cent[ii]+np.einsum('nij,nj->ni',ringrot[ii],U[change]-C[ii])
  rg1=cent[ii+1]+np.einsum('nij,nj->ni',ringrot[ii+1],U[change]-C[ii+1])
  y=(1-zz[:,None])*rg0+zz[:,None]*rg1
  delta=(y-orig[rep[change]])*smooth_boundary[:,None]
  prod[key,scope]=orig[scope]+delta[take]
  Y1=prod[key]
  edges=d['edge'+s]; e=E[edges]
  reg=lambda X:metric(X[e[:,0]]-X[e[:,1]])/metric(X0[e[:,0]]-X0[e[:,1]])
  X0=X; r0,r1=reg(orig),reg(Y1)
  bb=np.max(abs(Y1[d['footprint'+s]]-orig[d['footprint'+s]]))
  # Use same-source held reference to detect large rotation and degeneracy
  # as conservative alarms; not image judge.
  na=normals(orig,F[faces]);nb=normals(Y1,F[faces]);dd=(na*na).sum(1);fok=dd>1e-22
  area=(na[fok]*nb[fok]).sum(1)/dd[fok]
  case.append(dict(arcs=len(ringrot),minimum_ring_frame_det=float(np.linalg.det(ringrot).min()),edge_bad_before_after=[int(sum((x<.5)|(x>2))) for x in (r0,r1)],r_minmax=[float(r1.min()),float(r1.max())],old_edge_fails_untouched=int(sum(((r0<.5)|(r0>2))&keep[inv[e]].all(1))),frozen_pin_delta_m=float(bb),low_boot_mm=1000*float(Y1[d['boot'+s],2].min()),signed_source_area_under_point1=int(sum(area<.1)),signed_source_nonpositive=int(sum(area<=0)),max_vertex_delta_mm=1000*float(metric(delta).max())))
 maps.update({s+'material_weld':change,s+'ring_idx':ii,s+'ring_fraction':zz,s+'rest_offsets':offsets,s+'rest_ring_centers':C})
 report[s]={'ring_count':len(levels),'editable_shaft_quads':len(f),'mapped_positions':len(change),'rest_repro_m':float(metric(mapped0-U[change]).max()),'cases':case}
 print(s,report[s],flush=True)
with (P/'editable-internal-rest.obj').open('w') as o:
 at=1
 for side,name,v,f in meshes:
  o.write('o '+side+'_'+name+'\n')
  for p in v:o.write('v '+' '.join('%.9f'%k for k in p)+'\n')
  for a in f:o.write('f '+' '.join(str(int(k)+at) for k in a)+'\n')
  at+=len(v)
(P/'result.json').write_text(json.dumps(report,indent=2));np.savez_compressed(P/'surface-correspondence.npz',**maps)
np.savez_compressed(P/'numerical-poses-not-approved.npz',xyz=prod.astype(np.float32))
