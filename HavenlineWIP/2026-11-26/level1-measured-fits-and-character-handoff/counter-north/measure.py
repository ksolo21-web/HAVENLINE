import numpy as np,json,re,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]); d=root/'hvn-counter-recovery/donor'; scene=d/'north_counter_donor.tscn'; post=d/'gate_post.obj'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert H(scene)=='d830d85bc86b809b58cc9f3ff8a3a382db94cfe19ad8038d5b402b01acd482ea'
assert H(post)=='7cd6c9287741c50904a648589030e1a55dece1908a88f485b16195fc8937a893'
ls=scene.read_text(); pts=[]; f={}; mat=None
for l in post.read_text().splitlines():
 s=l.split()
 if not s:continue
 if s[0]=='v':pts.append([float(x) for x in s[1:4]])
 if s[0]=='usemtl':mat=s[1]; f.setdefault(mat,[])
 if s[0]=='f': f[mat].append([int(q.split('/')[0])-1 for q in s[1:]])
v=np.array(pts); W=3.175; pitch=W/13.; c=-3.25
native=root/'hvn-counter-recovery/compact-reach-v1/run.jdxCQmtk/counter.json'
assert H(native)=='7825ba134e6b13ce6539e3cbab16899f64a2cd83de0e085a50e6443fc08d36b4'
cnt=np.concatenate([np.array(m['positions']) for m in json.loads(native.read_text())])
get=lambda n:np.array([float(x) for x in re.search(fr'name="{n}"[^\n]*\nposition = Vector3\(([^)]*)\)',ls)[1].split(',')])
out={}
for key,sgn,plane in [('Left',1,-1.825),('Right',-1,1.825)]:
 cap=get(key+'ArchiveTimberCap'); flank=get('OriginalNorth'+key+'VisualCrop')
 L={}
 for mat,faces in f.items():
  q=v[np.unique([i for face in faces for i in face])]+cap
  q[:,0]=(q[:,0]-plane)*sgn
  L[mat]=[q.min(0).tolist(),q.max(0).tolist()]
 timber=v+cap; timber[:,0]=(timber[:,0]-plane)*sgn
 yz=[0,.95]+[p[1] for p in timber if 0<p[1]<.95]
 expected=[]
 for y in yz:
  hit=[]
  for ids in f['timber']:
   q=timber[ids]
   for a,b in zip(q,np.roll(q,-1,axis=0)):
    if min(a[1],b[1])<=y<=max(a[1],b[1]):
     if a[1]==b[1]:hit.extend([a[0],b[0]])
     else:hit.append(a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]))
  expected.append((min(hit),max(hit)))
 c_u=min((cnt[:,0]-plane)*sgn)
 spill=2*1.956-.012-W
 assert spill>.72
 # Normal start-to-end run boundaries are exact. Centers are a measured plan, not an emitted mesh.
 centers=-W+(np.arange(13)+.5)*pitch
 assert max(centers)<0 and min(centers)>-W
 assert abs((flank[0]-plane)*sgn+W/2)<1e-12
 assert min(-a for a,b in expected)>.007 and min(b-c_u for a,b in expected)>.007
 reservation=min(bounds[0][0] for bounds in L.values())-.002
 out[key.lower()]={'default_no_contact_signed_u_max_m':reservation,'terminal_center_to_no_contact_plane_m':float(reservation-centers[-1]),'world_cut_x_m':c+plane,'allow_new_flank_signed_u_m':[-W,0],
   'world_planned_centers_x_m':(c+plane+sgn*centers).tolist(),'cap_signed_u_y_z_bounds':L,
   'minimum_cap_timber_X_overlap_into_stock_flank_m':min(-a for a,b in expected),
   'minimum_cap_timber_X_overlap_past_donor_extreme_m':min(b-c_u for a,b in expected),
   'nearest_counter_donor_signed_u_m':c_u,'standard_double_residual_fails_m':spill}
pos={}
for n in ('SurvivingFenceLeft','CounterSealedBridge','SurvivingFenceRight','CustomerExteriorStance','WorkerInteriorStance','StockHandling','PaymentHandling','StockRestWitness','PaymentRestWitness'):pos[n]=get(n).tolist()
print(json.dumps({'north_z_world_m':1.80,'fixture_seed_hash':H(scene),'counter_geometry_hash':H(native),
 'fixed_barrier_and_anchors_local':pos,'signed_post_pitch_m':pitch,'plan':out,'analysis_only':True},indent=2))
