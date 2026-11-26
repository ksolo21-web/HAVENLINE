"""Build a detached fresh body binding from original indexed art; Python only."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
glb,out=map(Path,sys.argv[1:])
raw=glb.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(raw)=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
assert not out.exists();out.mkdir(mode=0o700)
n,k=struct.unpack_from('<II',raw,12);assert k==0x4e4f534a
G=json.loads(raw[20:20+n]);base=28+n
def get(i):
 a=G['accessors'][i];v=G['bufferViews'][a['bufferView']]
 d={5121:'<u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
 q={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 assert not v.get('byteStride')
 return np.frombuffer(raw,dtype=d,count=q*a['count'],offset=base+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,q)
p=G['meshes'][0]['primitives'][0];a=p['attributes']
V=get(a['POSITION']).astype(float);faces=get(p['indices']).reshape(-1,3)
assert len(V)==52898 and len(faces)==96001
skin=G['skins'][0]; names=[G['nodes'][j]['name'] for j in skin['joints']]
bind=np.linalg.inv(get(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1))
landmark=lambda key:bind[names.index(key),:3,3].copy()
N={}
def add(k,parent,h,t,channel,lim,deform=True):
 h,t=np.asarray(h),np.asarray(t)
 Z=(t-h)/np.linalg.norm(t-h)
 ref=np.array([0.,0.,1.]);X=np.cross(ref,Z)
 if np.linalg.norm(X)<.1:X=np.cross(np.array([0.,1,0]),Z)
 X/=np.linalg.norm(X);Y=np.cross(Z,X);R=np.stack([X,Y,Z],axis=1)
 assert np.linalg.det(R)>.999
 M=np.eye(4);M[:3,:3]=R;M[:3,3]=h
 N[k]=dict(parent=parent,global_bind=M.tolist(),tail=t.tolist(),deform=deform,control=channel,hard_prototype_limit_deg=lim)
def H(k):return np.asarray(N[k]['global_bind'])[:3,3]
add('Root',None,[0,0,0],[0,.08,0],'ground root',[-180,180],False)
add('Pelvis','Root',landmark('Hip'),landmark('Spine01'),'COM/root-relative shift',[-15,15])
add('Waist','Pelvis',landmark('Spine01'),landmark('Spine02'),'lower trunk',[-20,20])
add('Thorax','Waist',landmark('Spine02'),landmark('NeckTwist01'),'upper trunk',[-22,22])
add('Collar','Thorax',landmark('NeckTwist01'),landmark('Head'),'neck',[-24,24])
add('Head','Collar',landmark('Head'),[0,.79,.01],'head',[-35,35])
for s,sg in [('L',1),('R',-1)]:
 P=lambda key:landmark(s+'_'+key)
 add(s+'Hip','Pelvis',P('Thigh'),P('Calf'),'hip swing',[-40,45])
 add(s+'Shin',s+'Hip',P('Calf'),P('Foot'),'anterior knee hinge',[0,80])
 add(s+'CollarFlex',s+'Shin',P('Calf')*.44+P('Foot')*.56,P('Foot'),'calf-driven sleeve ring',[-18,18])
 add(s+'Heel',s+'Shin',P('Foot'),P('ToeBase'),'rigid foot/heel carrier',[-22,25])
 toe=P('ToeBase')
 add(s+'Ball',s+'Heel',toe,toe+np.array([.020*sg,-.006,.050]),'phalangeal ball articulation',[-18,22])
 add(s+'Clavicle','Thorax',P('Clavicle'),P('Upperarm'),'shoulder girdle',[-23,23])
 add(s+'Upper',s+'Clavicle',P('Upperarm'),P('Forearm'),'arm swing',[-100,115])
 add(s+'Forearm',s+'Upper',P('Forearm'),P('Hand'),'anatomical elbow',[0,115])
 add(s+'Mitt',s+'Forearm',P('Hand'),P('Hand')+np.array([.071*sg,0,-.005]),'wrist/rigid mitten',[-28,28])
 for k,land,ref in [('HeelTarget','Foot',[.0,-.014,-.057]),('BallTarget','ToeBase',[.0,-.012,.037]),('KneePole','Calf',[.0,.0,.16]),('PalmGrip','Hand',[.075*sg,-.014,.007])]:
  a0=P(land)+ref
  add(s+k,s+'Mitt' if k=='PalmGrip' else 'Root',a0,a0+[0,.035,0], 'contact socket / no vertex deformation',[0,0],False)
# Rigid attachment identity regions are the only use of original declared weights;
# nothing numeric from the old mixed skin is copied into the anatomical body bind.
OW=get(p['attributes']['WEIGHTS_0']); OJ=get(p['attributes']['JOINTS_0'])
hardware=[i for i,k in enumerate(names) if 'Fastener' in k]
cores={}
for j in hardware:
 q=names[j];loc=landmark(q); parent=q[0]+'Heel' if 'Boot' in q else 'Pelvis'
 new_id='Rigid_'+q
 add(new_id,parent,loc,loc+[0,.023,0],'rigid apparatus island',[0,0])
 ids=np.flatnonzero((OW*(OJ==j)).sum(1)>.9999)
 assert len(ids)>0
 cores[new_id]=ids
# Harmonic extension on the actual 1 micrometre welded source. Strong two-ended
# boot rolls etc are analytic anatomy fields, not reused rejected skin weights.
WV,weld=np.unique(np.round(V,6),axis=0,return_inverse=True)
m=len(WV);x,y,z=WV.T
deform=[k for k,v in N.items() if v['deform']]
K={k:i for i,k in enumerate(deform)}
F=np.zeros((m,len(K)),float)
def smooth(v):
 q=np.clip(v,0,1);return q*q*(3-2*q)
def blend(A,B,h,plo,phi,amount):
 a=smooth((h-plo)/(phi-plo))
 F[:,K[A]]+=amount*(1-a);F[:,K[B]]+=amount*a
# Anatomical body regions emerge from rest hip/shoulder/ankle planes. The stock
# character has mittens: no assumed digit controllers or bilateral sign mirroring.
leg=smooth((.327-y)/.075)
arm=smooth((abs(x)-.167)/.080)*smooth((y-.447)/.047)*(1-smooth((y-.565)/.040))
central=(1-leg)*(1-arm)
v=smooth((y-.313)/.052); q=smooth((y-.395)/.085); n=smooth((y-.539)/.090); h=smooth((y-.595)/.068)
for k,numer in [('Pelvis',1-v),('Waist',v*(1-q)),('Thorax',v*q*(1-n)),('Collar',v*q*n*(1-h)),('Head',v*q*n*h)]:F[:,K[k]]=central*numer
for s,sg in [('L',1),('R',-1)]:
 mside=smooth((sg*(x-.014)+.028)/.056)
 amount=leg*mside
 ankle=H(s+'Heel')[1];knee=H(s+'Shin')[1]
 outer=H(s+'Ball')
 plane=(WV-outer)@np.array([.18*sg,0.,.983667])
 toe=smooth((plane+.020)/.037)
 # Six anatomical partitions, with ball-isolation of the real low toe/heel sole.
 lower=smooth((y-ankle*.60)/(max(knee-ankle,.01)*.48))
 cuff=smooth((y-(ankle+.035))/.060)
 upper=smooth((y-(knee-.034))/.076)
 F[:,K[s+'Ball']]+=amount*(1-lower)*toe
 F[:,K[s+'Heel']]+=amount*(1-lower)*(1-toe)
 F[:,K[s+'CollarFlex']]+=amount*lower*(1-cuff)
 F[:,K[s+'Shin']]+=amount*lower*cuff*(1-upper)
 F[:,K[s+'Hip']]+=amount*lower*cuff*upper
 a=arm*mside
 v0=smooth((sg*x-.192)/.065); v1=smooth((sg*x-.269)/.067); v2=smooth((sg*x-.375)/.064)
 for k,val in [('Clavicle',1-v0),('Upper',v0*(1-v1)),('Forearm',v0*v1*(1-v2)),('Mitt',v0*v1*v2)]:F[:,K[s+k]]+=a*val
assert np.allclose(F.sum(1),1,atol=1e-12)
edge=np.unique(np.sort(weld[faces[:,[[0,1],[1,2],[2,0]]]].reshape(-1,2),axis=1),axis=0)
edge=edge[edge[:,0]!=edge[:,1]]
u,v=edge.T; length=np.linalg.norm(WV[u]-WV[v],axis=1)
w=1/np.maximum(length,.0001)
L=coo_matrix((np.r_[w,w],(np.r_[u,v],np.r_[v,u])),shape=(len(WV),len(WV))).tocsr()
degree=np.asarray(L.sum(1)).ravel()
# Use a fixed anchored diffusion, not a deformation fit, so old poses cannot bias the bind.
anchor={}
for k,i in cores.items():
 for row in np.unique(weld[i]):
  assert row not in anchor or anchor[row]==K[k]
  anchor[row]=K[k]
# Preserve pure true contacting low heel and distal balls, away from the roll window, with authored supports.
for s,sg in [('L',1),('R',-1)]:
 owner=sg*(x-.014)>.04
 for k,mask in [('Heel',z<H(s+'Ball')[2]-.048),('Ball',z>H(s+'Ball')[2]+.051)]:
  for row in np.flatnonzero(owner&(y<.017)&mask):anchor.setdefault(row,K[s+k])
pins=np.array(sorted(anchor));free=np.setdiff1d(np.arange(len(WV)),pins); C=np.zeros((len(pins),len(K))); C[np.arange(len(pins)),[anchor[j] for j in pins]]=1
alpha=.33
S=diags((1+alpha)*degree)-L
Y=F.copy();Y[pins]=C
Y[free]=spsolve(S[free][:,free],alpha*degree[free,None]*F[free]-S[free][:,pins]@C)
assert np.isfinite(Y).all() and np.min(Y)>-1e-10
Y=np.maximum(Y,0)
I=np.argsort(-Y,axis=1,kind='stable')[:,:4].astype(np.uint16)
Q=np.take_along_axis(Y,I,axis=1);lost=1-Q.sum(1);Q/=Q.sum(1,keepdims=True)
# Full seam duplicate equality is by welded index, not rounded after skinning.
WI=I[weld]; WT=Q[weld].astype(np.float32)
assert np.max(abs(WT.sum(1)-1))<2e-7
assert np.array_equal(WT[np.flatnonzero(np.isin(weld,pins))].sum(1),np.ones(int(np.isin(weld,pins).sum())))
for x in N:
 p0=N[x]['parent']
 if p0 is not None:N[x]['local_bind']=(np.linalg.inv(np.array(N[p0]['global_bind']))@np.array(N[x]['global_bind'])).tolist()
rig=dict(format='hvn-portable-rer-1',axes='Godot source Y up, +Z forward; new bone local +Z points down segment',model_sha256=sha(raw),new_bones=N,weighted_slots=deform,weight_encoding='4 uint16 joint IDs + 4 float32 positive weights, source vertex index order',locked_source_mesh=True,production=False)
(out/'rig.LOCAL.json').write_text(json.dumps(rig,separators=(',',':')))
np.savez_compressed(out/'skin.LOCAL.npz',joints=WI,weights=WT)
print(json.dumps(dict(status='NEW_AUTHORED_NEUTRAL_BIND_UNVALIDATED_MOTION',source_asset=sha(raw),preserved_original_vertices=len(V),preserved_original_triangles=len(faces),weld_solved_rows=len(WV),weight_sum_max_error=float(np.max(abs(WT.sum(1)-1))),weight_dropped_mass_p99_and_max=np.quantile(lost,[.99,1]).tolist(),fresh_joint_count=len(N),deform_count=len(deform),hardware_rigid_core_controls=len(cores),hard_anchor_rows=len(pins),joint_limits_native_enforced=False,local_payload_hashes={p.name:sha(p.read_bytes()) for p in sorted(out.iterdir())}),indent=2))
