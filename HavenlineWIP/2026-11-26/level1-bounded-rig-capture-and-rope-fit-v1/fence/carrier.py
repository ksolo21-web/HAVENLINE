from pathlib import Path
import hashlib,json, numpy as np
from collections import Counter
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parent;P=R.parent
S=P/'hvn-l1-fence-33036-seated-weave-proof-v1'
q=(R/'reduce.py').read_text(); C={'__file__':str(R/'reduce.py')}
exec(q[:q.index('pins=[0,')],C)
pairs=C['pairs'];d=np.load(C['NP']);V=d['position'];G=d['group']
def digest(n):return hashlib.sha256((P/n).read_bytes()).hexdigest()
pins={
 'hvn-l1-fence-33036-rooted-emboss-module-v1/module.py':'c92c7ee29ce2fc8c80435c795e7f77eec2039773aae9ef3824961c10b839aa2f',
 'hvn-l1-fence-meshy-bold-material-native-preflight-v1/staged/HavenlineLevel1/previews/r17_fence/r17_fence_view.gd':'3f39e92e161c9a1c7f14c859a18d9c48bca6e11139bc7354234aa8cb00ad1d47',
 'hvn-owner-fence-33036-33035/33035.png':'bd17e02a2999294e032d78ee93b61228658fae060da77c241934bd3fad0a01a8',
 'hvn-owner-fence-33036-33035/33036.png':'067b1e9f387882314094196dce1938f713875805f50902857499df6c376261e3',
 'hvn-owner-fence-33036-33035/33037.png':'a20a48ef36cc8d68aecd5ad87ce6a1ddc765e6052be1cac2a9e892a6c7eb464e',
 'hvn-owner-fence-33036-33035/33038.png':'1be05c57ad2fcfd088442516eee81d74cbffe8233e1394dceb88cbf47c59de00',

 'hvn-l1-fence-33036-west-lower-grade-v1/grade.py':'420ab4c91e3c8b12678c9b0442a29053c07717509fb8d2f8e5a1d8389b03d01a',
 'hvn-pad-mount-admission/isolated-source/HavenlineLevel1/accepted_t02_surface.gd':'23333fc7308d88fd4ed4cb9c9fadc3b94d3dc66838a966731fd32d3785711600',
 'hvn-pad-mount-admission/isolated-source/HavenlineLevel1/layout.json':'e3fc7eb561ae7288d4dc77ffc47b05cac924e8bb2dc2b99ec789a33d430f4458',
 'hvn-l1-gate-art-admission-protocol/triangles.py':'f0dbc0fd1f1be4c9356e95835553d93bd3a506447c8f74c883837fe594b1a301'
}
for n,h in pins.items():assert digest(n)==h
bound=C['pre']['ctx']['height']
fn=P/'hvn-l1-fence-33036-rooted-emboss-module-v1/module.py'
text=fn.read_text(); gt=(P/'hvn-l1-fence-33036-west-lower-grade-v1/grade.py').read_text()
D={'height':bound,'np':np}
exec('def h(p):return height(np.asarray(p))\n'+gt[gt.index('def cross(a,b)'):gt.index('vals=[]')],D)
exec(gt[gt.index('from functools'):gt.index('for i,tr in enumerate(lower):')],D)
F={'np':np,'G':D}
exec(text[text.index('def terrain_clip'):text.index('foot={k:terrain_clip')],F)
terrain=F['terrain_clip']
def loadobj(f):
 v=[];ix=[]
 for l in f.read_text().splitlines():
  if l.startswith('v '):v.append(list(map(float,l.split()[1:])))
  if l.startswith('f '):ix.append([int(i)-1 for i in l.split()[1:]])
 return np.array(v),np.array(ix)
assert hashlib.sha256((R/'ReducedWeave_Study.obj').read_bytes()).hexdigest()=='730538347f763a0c6fe4a3add5564325021605e75b387013f27b532042f8c81d'
Rope,fr=loadobj(R/'ReducedWeave_Study.obj')
npV=C['v']; groups=C['g']
rail=V[G=='rail_0'];xs=np.unique(rail[:,:,0]);ys=np.array([np.unique(rail[rail[:,:,0]==q,1]).mean() for q in xs])
lo,hi=xs[30],xs[40];pick=xs[30:41]
# Fresh solid rope-bearing support on the same graded station anchors. Front
# deck at exactly +103.4mm; broad rounded-ish chamfered profile retains depth.
sec=[(-.055,.1034),(.055,.1034),(.064,.079),(.064,.019),(.052,-.0097),(-.052,-.0097),(-.064,.019),(-.064,.079)]
railv=np.array([[x,y+dy,9.8+dz] for x,y in zip(pick,ys[30:41]) for dy,dz in sec])
N=len(sec); faces=[]
for i in range(len(pick)-1):
 for j in range(N):
  a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j
  faces.extend(((a,b,c),(a,c,d)))
for j in range(1,N-1):
 faces.extend(((0,j+1,j),((len(pick)-1)*N,(len(pick)-1)*N+j,(len(pick)-1)*N+j+1)))
faces=np.array(faces);B=railv[faces]
if np.einsum('ij,ij->i',B[:,0],np.cross(B[:,1],B[:,2])).sum()<0:faces=faces[:,::-1];B=railv[faces]
add=Counter((a,b) for f in faces for a,b in zip(f,np.roll(f,-1)))
assert all(n==1 and add[(b,a)]==1 for (a,b),n in add.items())
def support(T):
 base=np.unique(T[np.isclose(T[:,:,2],9.9034,rtol=0,atol=2e-12)],axis=0)
 assert len(base)==4
 # Entire convex planar pad footprint lies on the supporting carrier face.
 yy=np.interp(base[:,0],pick,ys[30:41])
 assert np.max(abs(base[:,1]-yy))<.055 and base[:,0].min()>lo and base[:,0].max()<hi
 return list((1000*np.array([base[:,0].min()-lo,hi-base[:,0].max(),.055-max(abs(base[:,1]-yy))])).tolist())
seat_geometry={k:npV[np.array(groups[k])] for k in ('fitted_seat_0','fitted_seat_1')}
local={k:pairs(B,V[G==k]) for k in ('upper-placeholder',) if False}
for k in ('body','caps','rail_1','rear_0','rear_1'):local[k]=pairs(B,V[G==k])
# Actual end-side seam compatibility is a separate boundary condition.
# The section does not replace the untouched old flanks by author fiat.
flank=(rail[:,:,0].max(1)<=lo)|(rail[:,:,0].min(1)>=hi)
old=rail[flank]
cross=B
baseline=rail[(rail[:,:,0].min(1)>=lo)&(rail[:,:,0].max(1)<=hi)]
comparison=pairs(baseline,V[G=='body'])
seams=[]
for x in (lo,hi):
 a=np.unique(rail[rail[:,:,0]==x],axis=0)
 b=railv[railv[:,0]==x]
 seams.append({'x':float(x),'old_new_front_max_difference_mm':float((a[:,2].max()-b[:,2].max())*1000),'old_new_back_min_difference_mm':float((a[:,2].min()-b[:,2].min())*1000),'status':'exact same axle, not equal plane profile'})
out=dict(state='detached physical bearing + carrier source, mount HOLD whenever exact protected intersection is unclassified',
 bay_x=[float(lo),float(hi)],baseline_bay_body_contact=comparison,end_plane_profiles=seams,triangles=len(B),closed=True,
 seat_deck={k:dict(xmin_max_y_clear_mm=support(T),strict_crossing=pairs(B,T)) for k,T in seat_geometry.items()},
 carrier_rope=pairs(B,Rope[fr]),separate_protected_parts=local,unaltered_flank_boundary=pairs(B,old),
 terrain_indexed={k:terrain(T) for k,T in [('new_carrier',B),('reduced_rope',Rope[fr]),*seat_geometry.items()]})
print(json.dumps(out,indent=2))
# Preserve this as neutral detached source evidence only. Do not call it a
# complete topology even if its deck supports both seat foot polygons.
lines=['# detached carrier, protected mount diagnostic']+['v '+' '.join(f'{x:.12f}' for x in p) for p in railv]
lines+=['f '+' '.join(str(x+1) for x in f) for f in faces]
(R/'DetachedCarrier_HOLD.obj').write_text('\n'.join(lines)+'\n')
