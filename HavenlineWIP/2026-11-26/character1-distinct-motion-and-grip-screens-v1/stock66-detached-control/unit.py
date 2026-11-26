"""One in-memory stock66 sole carrier architecture diagnostic; no art/clip export."""
from pathlib import Path
import hashlib,json,re,math
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parent.parent
O=P/'hvn-l1-c1-stock66-shared-transfer-geometry-v1/transfer.py'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(O.parent/'SHA256SUMS')=='d46e52994f8c64365da0d6196e23b453fc74fc16e8f1a5decaa3cfaae299246c'
assert sha(O)==next(l.split()[0] for l in (O.parent/'SHA256SUMS').read_text().splitlines() if l.endswith(' transfer.py'))
old=O.read_text()
# Reuse only exact source-loading and indexed ground clip code. Never old pose solver.
ns={'__file__':str(O)}
exec(compile(old[:old.index('design=json')],str(O),'exec'),ns)
exec(compile(old[old.index('def support_fragments'):old.index('if len(todo)==2:')],str(O),'exec'),ns)
S,F,J,W,ip,names,decode=[ns[n] for n in ('S','F','J','W','ip','names','decode')]
support=ns['support_fragments']; gap=ns['exact_gap']; ground=ns['ground']
AR=P/'hvn-l1-c1-stock-walk-adjacent-native-v1/native.F8xorDH1'; BR=ns['ns']['N']
def tr(v):
 m=np.eye(4);m[:3,3]=v;return m
def mat(r,a,b):
 x=np.eye(4);x[:3,:3]=r;x[:3,3]=b-r@a;return x
def unit(v):return v/np.linalg.norm(v)
def roll(deg):return Rotation.from_euler('z',deg,degrees=True).as_matrix()
def align(a,b):
 a,b=unit(a),unit(b);c=np.cross(a,b);s=np.linalg.norm(c)
 return Rotation.from_rotvec(c/s*math.atan2(s,a@b)).as_matrix() if s>1e-12 else np.eye(3)
first=json.loads((AR/'walk-trace-only/palette.json').read_bytes())
rests=np.array([decode(r['rest']) for r in first['bindings']])
nj=J.copy(); nw=W.copy()
virtual=[]; dictionaries={}; topology={}
thresholds=[-.072,-.027,.052,.100]
for f in 'LR':
 fi,ti=names[f+'_Foot'],names[f+'_ToeBase']
 related=(W*np.isin(J,[fi,ti])).sum(1)
 # Only actual outsole rows, >0.92 original sole influence and <12 standardized
 # art-mm y. No cloth or upper row treatment; deliberate narrow novel unit.
 mask=(related>.92)&(S[:,1]<.012)
 assert mask.sum()>500
 ids=[]; pivots=[]
 center=np.median(S[mask,0])
 for n,z in zip(('heel','midfoot','ball','toe'),thresholds):
  # Each pivot is anchored to an actual existing undeformed unit vertex;
  # identity rig rest product is unchanged after appending new controls.
  region=np.flatnonzero(mask)
  p0=int(region[np.argmin((S[region,0]-center)**2+(S[region,2]-z)**2)])
  m=tr((ip[fi]@np.r_[S[p0],1])[:3])
  k=len(ip)+len(virtual);virtual.append((f,n,fi,m,np.linalg.inv(m)@ip[fi],p0))
  ids.append(k);pivots.append(p0)
 z=S[mask,2]
 lo=np.maximum(0,np.minimum(2,np.searchsorted(thresholds,z,side='right')-1))
 a=np.clip((z-np.array(thresholds)[lo])/(np.array(thresholds)[lo+1]-np.array(thresholds)[lo]),0,1)
 alpha=np.rint(W[mask].sum(1)*65535).astype(int)
 wt=np.rint(alpha*a).astype(int)
 nj[mask]=np.c_[np.array(ids)[lo],np.array(ids)[lo+1],np.zeros((mask.sum(),2),int)]
 nw[mask]=np.c_[(alpha-wt)/65535,wt/65535,np.zeros((mask.sum(),2))]
 dictionaries[f]=(mask,ids,pivots)
 topology[f]={'outsole_changed_rows':int(mask.sum()),'distinct_carrier_rows_nonzero':{n:int(((nj[mask]==k)&(nw[mask]>0)).any(1).sum()) for n,k in zip(('heel','midfoot','ball','toe'),ids)},
   'pivots_original_vertex_rows':pivots,'sole_weight_table_rows_sha256':hashlib.sha256(np.c_[np.flatnonzero(mask),nj[mask],nw[mask]].astype('<f8').tobytes()).hexdigest()}
extra_ip=np.array([v[4] for v in virtual])
ip2=np.concatenate((ip,extra_ip))
def extend(g):return np.concatenate((g,np.array([g[j]@m for _,_,j,m,_,_ in virtual])))
sr=np.c_[S,np.ones(len(S))]
def skin(g,ii,j,w):
 return np.einsum('nwij,nj,nw->ni',(g@ii)[j],sr,w)[:,:3]+S*(1-w.sum(1,keepdims=True))
rest=skin(rests,ip,J,W);rest_new=skin(extend(rests),ip2,nj,nw)
err=float(np.linalg.norm(rest-rest_new,axis=1).max()*1000)
assert err<.0001
assert np.max(abs(nw.sum(1)-W.sum(1)))<1e-7
assert (nw>0).sum(1).max()<=4
assert not np.any(dictionaries['L'][0]&dictionaries['R'][0])
# Unchanged position/index/UV/material in immutable source. No skin influence
# writes on knee/calf hardware anchored rows; still measure their posed shape.
hw=[k for n,k in names.items() if 'Fastener' in n or 'KneePad' in n]
hardware=((W*np.isin(J,hw)).sum(1)>.5)
maskall=dictionaries['L'][0]|dictionaries['R'][0]
assert not np.any(hardware&maskall)
import sys
if sys.argv[1:]==['--emit-table']:
 print('original_imported_row,side,carrier_a,carrier_b,quantized_weight_a,quantized_weight_b')
 for side in 'LR':
  mask,ids,pivot=dictionaries[side]
  for r in np.flatnonzero(mask):
   a,b=nj[r,:2];wa,wb=np.rint(nw[r,:2]*65535).astype(int)
   print(f'{r},{side},{virtual[a-66][1]},{virtual[b-66][1]},{wa},{wb}')
 sys.exit()
assert not sys.argv[1:]
import struct
gf=P/'hvn-pad-mount-admission/isolated-source/HavenlineLevel1/assets/characters/Character1.glb'
data=gf.read_bytes();assert hashlib.sha256(data).hexdigest()=='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
gltf=json.loads(data[20:20+struct.unpack_from('<I',data,12)[0]]);gl_nodes=gltf['nodes']
pa={gl_nodes[i]['name']:k['name'] for k in gl_nodes for i in k.get('children',[])}
def line(n):
 while n in pa:
  yield n;n=pa[n]
 yield n
calc=[]
for estate,tt,f in [(BR,20,'L'),(AR,160,'R')]:
 d=estate/'walk-trace-only'
 dat=json.loads((d/'palette.json').read_bytes())
 r=next(y for y in dat['rows'] if y['tick']==tt)
 Mesh=decode(r['mesh']); Bs=decode(r['skeleton']); ib=np.linalg.inv(Bs)
 g=np.array([decode(v[0]) for v in r['pose_and_product_by_slot']])
 baseW=extend(g)
 def world(x):
  return x@Mesh[:3,:3].T+Mesh[:3,3]
 stock=world(skin(g,ip,J,W))
 native=d/f'{tt}-s0-baked.f32'
 assert sha(native)==dat['streams'][native.name]['sha256']
 ref=world(np.fromfile(native,'<f4').reshape(-1,3));assert np.max(np.linalg.norm(stock-ref,axis=1))<=.00005
 copied=world(skin(baseW,ip2,nj,nw))
 mask,ids,pivots=dictionaries[f]
 Heel=(nj==ids[0])&(nw>0)
 contact=np.flatnonzero(mask&(S[:,2]>=.043)&(S[:,2]<=.062))
 edge_faces=ns['ns']['groups'][f][1]
 other_foot='R' if f=='L' else 'L'
 # Independently rotate new toe carrier around the actual ball pivot,
 # keeping all other posed carriers completely stationary.
 toe=ids[-1];ball=ids[-2];TM=Bs@baseW[toe];BH=(Bs@baseW[ball])[:3,3]
 pulse=baseW.copy();pulse[toe]=ib@mat(roll(10),BH,BH)@TM
 moved=world(skin(pulse,ip2,nj,nw))-copied
 no_toe=~(((nj==toe)&(nw>0)).any(1))
 assert np.max(np.linalg.norm(moved[no_toe],axis=1))<1e-10
 toe_max=float(np.linalg.norm(moved,axis=1).max()*1000)
 dom=(((nj==toe)*nw).sum(1)>.70)
 toe_median=float(np.median(moved[dom,1])*1000)
 # One named ball contact, select an actual small source sole triangle with
 # barycentric control, not a previous worn global penetration minimum.
 # Its original scene XZ is the frozen target for this test.
 ts,cs,fs=[names[f+x] for x in ('_Thigh','_Calf','_Foot')]
 hi,knee,ankle=[(Bs@g[i])[:3,3] for i in (ts,cs,fs)]
 lower=(S[:,1]<.010)&mask
 tri=ns['ns']['src'][F]; c=tri.mean(1)
 region=np.flatnonzero(lower[F].all(1)&(c[:,2]>.041)&(c[:,2]<.062)&(np.abs(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])[:,1])>1e-7))
 assert len(region)>0 and len(contact)>0
 mid=np.median(S[mask,0]);face=int(region[np.argmin((c[region,0]-mid)**2+(c[region,2]-.052)**2)])
 anchor=copied[F[face]].mean(0)
 target=anchor.copy();target[1]=ground(anchor[0],anchor[2])+.00015
 RR=roll(-6) # forefoot rocker, independent toe carrier counterflexes +10
 goal=target-(RR@(anchor-ankle))
 ll=np.array([np.linalg.norm(knee-hi),np.linalg.norm(ankle-knee)])
 r0=dict(tick=tt,loaded=f,foot_ball_face=face,barycentric=[1/3]*3,ground_target_xyz_m=target.tolist(),
   sole_toe_pulse_degrees=10,isolated_toe_max_world_mm=toe_max,
   toe_dominant_signed_median_up_mm=toe_median, heel_and_non_toe_rows_delta_mm=float(np.max(np.linalg.norm(moved[no_toe],axis=1))*1000),
   target_rest_skin_base_limb_lengths_mm=(ll*1000).tolist(),total_leg_reach_margin_mm=float(1000*(ll.sum()-np.linalg.norm(goal-hi))))
 dv=goal-hi;dist=np.linalg.norm(dv);nn=dv/dist
 if not abs(ll[0]-ll[1])<dist<ll.sum():
  r0.update(status='HOLD unreachable under original joint lengths',knee=None,clearance=None)
  calc.append(r0);continue
 axial=(ll[0]**2-ll[1]**2+dist**2)/(2*dist)
 outward=-.15 if f=='L' else .15
 pf=np.array([1.,0.,outward]);pole=unit(pf-nn*(pf@nn))
 k1=hi+nn*axial+pole*np.sqrt(ll[0]**2-axial**2)
 assert np.max(abs(np.array([np.linalg.norm(k1-hi),np.linalg.norm(k1-goal)])-ll))<1e-10
 r0['forward_knee_projection_mm']=float((k1-hi-nn*axial)[0]*1000)
 Ta=mat(align(knee-hi,k1-hi),hi,hi)
 Ca=mat(align(ankle-knee,goal-k1),knee,k1)
 Fa=mat(RR,ankle,goal)
 newg=g.copy()
 for n,k in names.items():
  a=set(line(n))
  if f+'_Foot' in a:mv=Fa
  elif f+'_Calf' in a:mv=Ca
  elif f+'_Thigh' in a:mv=Ta
  else:continue
  newg[k]=ib@mv@Bs@g[k]
 final=extend(newg)
 bp=(Bs@final[ball])[:3,3];final[toe]=ib@mat(roll(10),bp,bp)@Bs@final[toe]
 posed=world(skin(final,ip2,nj,nw))
 pnow=posed[F[face]].mean(0);r0['observed_ball_witness_xyz_residual_mm']=((pnow-target)*1000).tolist()
 for foot in 'LR':
  feet=ns['ns']['groups'][foot][1]
  res,_=gap(feet,posed)
  r0[foot]={'signed_min_mm':float(res[0]*1000),'min_face':res[1],'true_0_2_mm_band':support(feet,posed)}
 changed=np.linalg.norm(stock-posed,axis=1)>1e-8
 ix=F[changed[F].any(1)]
 ifaces=F[(changed[F].any(1))&(hardware[F].any(1))]
 def distort(ids):
  a,b=stock[ids],posed[ids]
  ea=np.linalg.norm(a-np.roll(a,1,axis=1),axis=2);eb=np.linalg.norm(b-np.roll(b,1,axis=1),axis=2)
  ratio=eb[ea>=.001]/ea[ea>=.001]
  n0=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);n1=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0])
  return dict(faces=len(ids),minmax_ratio_ge1mm=[float(ratio.min()),float(ratio.max())] if len(ratio) else [],
     opposed_world_normals=int(((n0*n1).sum(1)<0).sum()))
 r0.update(full_changed_rows=int(changed.sum()),neighbor_distortion=distort(ix),
    hardware_incident_changed=distort(ifaces),raw_hardware_weights_changed=0,
    hardware_max_world_delta_mm=float(np.linalg.norm((posed-stock)[hardware],axis=1).max()*1000),
    status='HOLD if any required support, other-sole, deformation or knee gate fails')
 calc.append(r0)
print(json.dumps(dict(rest_shape_max_delta_art_mm=err,regions=topology,hardware_source_rows=int(hardware.sum()),
  hardware_weights_immutable=True,walk_patch_results=calc,asset_generation=False,no_stock_mutation=True),indent=2))
