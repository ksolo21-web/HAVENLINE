"""Private material correspondence / cage feasibility; no model or action exporter."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
p=Path(__file__).resolve().parent
base=p.parent/'hvn-l1-c1-stride-broad-repair-v1'
M=base/'SHA256SUMS';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(M)=='649df17ed50eadcd56cd8077f8ad16dc7bee314282d8efbaf14cc396af9d49f2'
for row in M.read_text().splitlines():
 h,n=row.split('  ',1);assert sha(base/n)==h
D=np.load(base/'pose-inputs.npz')
R=D['rest'];frames=D['xyz']; S=D['scale']; o=D['offset']; E=D['edge']; F=D['tri']
weights=dict(zip(D['weight_names'],D['weights']))
_,weld=np.unique(np.rint(R/1e-6).astype('int64'),axis=0,return_inverse=True)
norm=lambda v: np.linalg.norm(v,axis=-1)
smooth=lambda x: np.clip(x,0,1)**3*(10+np.clip(x,0,1)*(-15+6*np.clip(x,0,1)))
def wrangle(x,axes):
 ix=np.column_stack([np.clip(np.searchsorted(a,x[:,j],side='right')-1,0,len(a)-2) for j,a in enumerate(axes)])
 lo=np.column_stack([a[ix[:,j]] for j,a in enumerate(axes)])
 hi=np.column_stack([a[ix[:,j]+1] for j,a in enumerate(axes)])
 f=(x-lo)/(hi-lo);assert np.all((-1e-8<=f)&(f<=1.00000001))
 order=np.argsort(-f,axis=1,kind='stable')
 dv=np.eye(3,dtype=int)[order]
 tr=np.stack((ix,ix+dv[:,0],ix+dv[:,0]+dv[:,1],ix+1),axis=1)
 sf=np.take_along_axis(f,order,axis=1)
 weights=np.column_stack((1-sf[:,0],sf[:,0]-sf[:,1],sf[:,1]-sf[:,2],sf[:,2]))
 return tr,weights
def apply(nodes,tr,w):
 k=nodes[tuple(tr.transpose(2,0,1))]
 return np.einsum('ijk,ij->ik',k,w)
def determinant(nodes,tr):
 t=nodes[tuple(tr.transpose(2,0,1))]
 return np.linalg.det(t[:,1:]-t[:,:1])
# Fixed ring lattice: square circumferential stations plus core and interior
# cross stations; volume is entirely hidden. Same interpolation on shared
# faces in consistent Freudenthal decomposition, never resample visible mesh.
from itertools import product,permutations
def all_tets(a):
 tr=[]
 for x in product(*[range(len(u)-1) for u in a]):
  b=np.array(x)
  for order in permutations(range(3)):
   m=np.eye(3,dtype=int)[list(order)]
   tr.append([b,b+m[0],b+m[0]+m[1],b+1])
 return np.array(tr)
C={}
out={'scale':float(S),'source_topology_vertices':len(R),'three_original_keys':[0,75,150],'rest_preflight':{},'states':[]}
for s in ('L','R'):
 own=sum(weights.get(s+'_'+name,0) for name in ('Foot','ToeBase','Calf','CalfTwist01','CalfTwist02','Thigh'))
 # Parameter support is pure rest position. Side source weights choose one
 # contiguous lower component but do not drive its internal deformation.
 # Protect dressed fastener skin by retaining exact source vertices & UVs.
 elig=(own>.55)&(R[:,2]<.40)&(R[:,2]>=0)&((R[:,0]>0) if s=='L' else (R[:,0]<0))
 minz=float(R[D['boot'+s],2].min())
 fixed=np.zeros(len(R),bool); ids=D['boot'+s];fixed[ids[R[ids,2]<minz+.030]]=True
 fixed[D['phase'+s]]=True
 for name,ws in weights.items():
  if name.startswith(s+'_BootFastener_'):fixed[ws>.001]=True
 for fr in frames:
  f=D['contact'+s];sel=((fr[f,2]>=-.001)&(fr[f,2]<=.002)).all(1)
  fixed[np.unique(f[sel])]=True
 locked=np.zeros(len(set(weld)),bool);locked[weld[fixed|~elig]]=True
 m=(~locked[weld])&elig
 vix=np.flatnonzero(m)
 v=R[m];a=v.min(0);b=v.max(0)
 ax=(np.linspace(a[0]-.02,b[0]+.02,7),np.linspace(a[1]-.02,b[1]+.02,7),np.array([-.01,.023,.045,.073,.104,.135,.175,.225,.283,.344,.401,.421]))
 cells=np.stack(np.meshgrid(*ax,indexing='ij'),axis=-1)
 tetra=all_tets(ax); tr,ww=wrangle(v,ax)
 dt=determinant(cells,tetra)
 recovered=apply(cells,tr,ww)
 rest_err=float(norm(recovered-v).max())
 assert rest_err<1e-10 and (abs(dt)>1e-7).all()
 # Positive control: exactly known affine rotation/shear/translation, plus
 # explicit inverted lattice red control.
 M=np.array([[1.02,.06,.01],[-.04,.99,.02],[.00,.01,1.04]])
 shift=np.array([.013,-.007,.022])
 control=apply(cells@M.T+shift,tr,ww)
 assert norm(control-(v@M.T+shift)).max()<1e-10
 inv=cells.copy();inv[3,:,:,0]=cells[5,:,:,0]
 assert np.any(determinant(inv,tetra)/dt<=0)
 # Shared positional seam check. Use common frame interpolation and common
 # blend coefficient across coincident source rows; no averaging edits.
 _,first=np.unique(weld[vix],return_index=True); same=weld[vix][first]
 rank=np.searchsorted(same,weld[vix]); assert np.all(same[rank]==weld[vix])
 master=first[rank]
 seam_delta=max(norm(recovered-recovered[master]))
 assert seam_delta<1.8e-6
 # Classifier is 1 between ankle & lower shin and C2 in spatial taper; sole
 # rows stay original stock, handoff retains exact visible asset/hardware.
 taper=smooth((v[:,2]-(minz+.032))/.046)*smooth((.372-v[:,2])/.088)
 C[s]=(vix,ax,cells,tetra,dt,tr,ww,taper,master,fixed)
 out['rest_preflight'][s]={'embedded_rows':len(v),'tetrahedra':len(tetra),'rest_error_m':rest_err,
   'affine_control_error_m':float(norm(control-(v@M.T+shift)).max()),
   'negative_inverted_or_collapsed':int((determinant(inv,tetra)/dt<=0).sum()),'rest_seam_rounding_max_m':float(seam_delta)}
if '--preflight' in sys.argv:
 print(json.dumps(out,indent=2));sys.exit(0)
Ys=[]
for k,X in enumerate(frames):
 Y=X.copy(); state={}
 for s,(ids,ax,nodes,tets,refdt,tr,ww,taper,master,fixed) in C.items():
  n=nodes.reshape(-1,3);z=n[:,2]
  # Driver is continuous in rest axial parameter, not a new visible weight
  # patch: foot and shank existing bind affines at protected exact keys.
  # There is a broad axial overlap, no fixed per-edge or cage anchor tweaks.
  frac=smooth((z-.093)/.177)
  def transform(name,n):
   ii=list(D['weight_names']).index(s+'_'+name)
   M=D['skin_world'][k,ii]
   return ((n/S+o)@M[:3,:3].T+M[:3,3]-o)*S
  proxy=(transform('Foot',n)*(1-frac[:,None])+transform('Calf',n)*frac[:,None]).reshape(nodes.shape)
  dr=determinant(proxy,tets)/refdt
  state[s]={'proxy_min_det':float(min(dr)),'proxy_nonpositive_tets':int((dr<=0).sum())}
  state[s]['first_inverted_cell_indices']=tets[np.where(dr<=0)[0][:1]].tolist()
  # Do not pose any visible vertex through an inverted cage.
  if np.any(dr<=0):continue
  embedded=apply(proxy,tr,ww)
  correction=(embedded-X[ids])*taper[:,None]
  correction=correction[master]
  Y[ids]=X[ids]+correction
  assert np.array_equal(Y[fixed],X[fixed])
  ev=D['left_ids' if s=='L' else 'right_ids'];ij=E[ev]
  r=norm(Y[ij[:,0]]-Y[ij[:,1]])/norm(R[ij[:,0]]-R[ij[:,1]])
  affected=np.isin(F,ids).any(1)
  ac=np.flatnonzero(affected)
  v=Y[F[ac]];rest=R[F[ac]];old=X[F[ac]]
  cross=lambda a:np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0])
  base_n=cross(rest); prev=cross(old); normals=prev/np.maximum(norm(prev)[:,None],1e-14)
  valid=norm(base_n)>1e-9
  ar=(cross(v)*normals).sum(1)/np.maximum(norm(base_n),1e-14)
  state[s].update({'edge_min':float(min(r)),'edge_max':float(max(r)),
    'edge_rails_failed':int(((r<.5)|(r>2.0)).sum()),'affected_area_rails_failed':int((valid&((ar<.5)|(ar>2))).sum()),
    'detected_face_reversals':int((valid&(ar<=0)).sum()),'maximum_posed_delta_mm':float(norm(correction).max()*1000),
    'lowest_stock_or_cage_boot_mm':[float(q[D['boot'+s],2].min()*1e3) for q in (X,Y)],'protected_pin_byte_exact':bool(np.array_equal(Y[fixed],X[fixed]))})
 Ys.append(Y);out['states'].append(state)
np.savez_compressed(p/'visible-diagnostic-arrays.npz',xyz=np.stack(Ys))
print(json.dumps(out,indent=2))
