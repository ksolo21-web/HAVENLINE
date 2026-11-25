from pathlib import Path
import numpy as np, math,hashlib,subprocess,runpy,json
R=Path(__file__).resolve().parent.parent
p=R/'hvn-l1-near-flight-live-body-observer-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='7688c8843dc45af01e8212304615e6652841dbbdd49c8b77cc32aba064334f08'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=p,check=True)
orig=(R/'hvn-l1-actual-near-flight-first-result-v1/native.log').read_text().splitlines()
now=(p/'native.txt').read_text().splitlines()
matches=lambda a:[l for l in a if l.startswith(('PFX_OBS ','EXAM_ADMISSION_PREFIX ','EXAM_FLIGHT_GEOM_HOLD '))]
raw=Path(__import__("sys").argv[1]).read_text().splitlines()
assert matches(orig)==matches(raw) and [l for l in raw if l.startswith("PFX_OBS ")] and sum(l.startswith("PFX_OBS ") for l in raw)==57
assert all(l in raw for l in now)
def get(t):
 l,=[l[len(t)+1:] for l in now if l.startswith(t+' ')]
 return json.loads(l)
x=get('EXAM_SUPPORT_INPUT'); g=get('EXAM_SUPPORT_GAPS')
assert x['tick']==1333 and np.allclose(x['pad_m'],.025,atol=1e-9) and x['needle_m']==.00008 and g['i']==0
guard=(R/'hvn-l1-actual-near-flight-candidate-v1/guard.gdfrag').read_text()
assert 'expected_body=grown_box(live_box[0],BODY_PAD)' in guard and 'BODY_PAD := Vector3(.025,.025,.025)' in guard
assert 'EXAM_SUPPORT_UNEXPECTED_PASS no dispatch' in (p/'prepare.py').read_text()
def pose(t): return np.array(t[0]),np.array(t[1:]).T
def gs(z):
 A=z[:,0]/np.linalg.norm(z[:,0]); B=z[:,1]-A*(A@z[:,1]); B/=np.linalg.norm(B)
 C=np.cross(A,B); assert C@z[:,2]>0
 return np.column_stack([A,B,C])
orig0,M=pose(x['mount']); iM=np.linalg.inv(M); vaxis=iM[0]
plan=x['plan'][0]; ages=plan['age_ticks']; assert ages==[0,20,110,130]
pS,S=pose(plan['source']); pD,D=pose(plan['rest']); K=np.array(plan['key'])
assert np.array_equal(K[0],pS) and np.array_equal(K[3],pD)
boxmin,boxmax=np.array(x['body_padded_m'])
q=(K[1:3]-orig0)@iM.T
lo=q.min(0)-.23545; hi=q.max(0)+.23545
legacy=np.column_stack([boxmin-hi,lo-boxmax]).ravel()
assert np.max(abs(legacy-g['signed_face_m'][1]))<1e-6
tri,c=runpy.run_path(str(R/'hvn-l1-transfer-crown-spacing-v1/audit.py'))['decode'](R/'havenline-rendered-wood-ab-verified/project/assets/studio/starter_ground_wood_lod.glb')
pts=np.unique(tri.reshape(-1,3),axis=0)
assert len(pts)==834 and sum(c)==1300
radius=np.linalg.norm(pts,axis=1).max()
A,C=gs(S),gs(D); U=A.T@C
ang=math.acos(np.clip((np.trace(U)-1.)/2.,-1,1))
axis=np.array([U[2,1]-U[1,2],U[0,2]-U[2,0],U[1,0]-U[0,1]])/(2*math.sin(ang))
T=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
rot=lambda u: np.eye(3)+math.sin(u*ang)*T+(1-math.cos(u*ang))*(T@T)
assert np.max(abs(rot(1)-U))<1e-9
res=A.T@S-np.eye(3); rho=np.linalg.norm(res,2); dr=np.linalg.norm(D-C,2)
N=8192
# Exact independent world projection derivative bound along the shared negative-X normal.
kn=K[2]-K[1]
L=np.linalg.norm(vaxis)*radius*(ang*(1+rho)+rho)+abs(vaxis@kn)
err=L/(2*N)+np.linalg.norm(vaxis)*(radius*dr+22e-6)
def gap(u):
 V=A@rot(u)@(np.eye(3)+(1-u)*res)
 return boxmin[0]-(max(pts@(V.T@vaxis))+vaxis@(K[1]+u*kn-orig0))
minimum=min(gap(j/N) for j in range(N+1))-err
assert minimum>=.098836
print(json.dumps(dict(negative_x_bound_unchanged_actual_25mm_box_mm=1000*minimum,old_broad_negative_x_mm=1000*g['signed_face_m'][1][0],same_exact_phase_b_prefix_hashes=57,
 shortest_turn_degrees=math.degrees(ang),asset_vertices=len(pts),ticks=ages,
 subdivisions=N,source_residual_op_norm=rho,projected_inflation_mm=err*1000,future_unverified=True),indent=2))
