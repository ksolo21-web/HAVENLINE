"""Offline current marker facing readback using prior independent strict verifier."""
import json, sys, hashlib
from collections import Counter
from pathlib import Path
import numpy as np
P=Path(sys.argv[1]); LIB=Path(sys.argv[2]); R=json.loads((P/'result.json').read_text()); names=R['measurements']
assert hashlib.sha256(LIB.read_bytes()).hexdigest()=='3fd21560d24d14a22cd5d8485cd638cdb4ab85c7078889413547bfe5a515205c'
code=LIB.read_text()
libs={'__name__':'offline_fixture_library'}
sys.argv=[sys.argv[0],str(P)]
# Reuse exact verified intersection recipe, not the producer's checker.
first=code.split("f=raw/'counter.json';")[0]; first=first.replace("(p/'native-v3-geometry.json')","(p/'result.json')")
exec(compile(first,str(LIB),'exec'),libs)
libs['raw']=P/'native';h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert h(P/'native/counter.json')==R['same_donor_import_sha256']
D=libs['tr'](P/'native/counter.json');libs.update(D=D)
DN,nD=libs['vectors'](D);libs.update(DN=DN,nD=nD,DL=D.min(1),DH=D.max(1))
exec(compile('def key(lo,hi):'+code.split('def key(lo,hi):',1)[1].split('state={}')[0],str(LIB),'exec'),libs)
route=(P/'native-route.log').read_text().splitlines();assert sum(s.startswith('PASS ') for s in route)==181 and not any(s.startswith('FAIL ') for s in route)
assert not (P/'native/save-artifacts.txt').read_bytes() and 'checks=181 failures=0 no_image_stages=24' in route[-1]
ids=[i for i in names if i.startswith('facing-')]
assert len(ids)==14
data={}
for k,m in names.items():
 f=P/'native'/(k+'.json')
 assert h(f)==m['born_from_actual_mesh_sha256']
 A=libs['tr'](f)
 c=libs['run'](A)[0];g=libs['conservative_slab_min'](A,1 if 'inboard' in k else -1)
 assert c==m['all_donor_pairs'] and abs(g-m['conservative_signed_z_gap_m'])<1e-10,k
 data[k]={'full_donor_strict_pairs':c,'signed_conservative_slab_gap_m':g}
 print(k,c,g,file=sys.stderr)
same={}
for k,w in R['analytic_same_foot_sideways_controls'].items():
 S=np.array(names[k]['native_angle']['actor_foot']);k0='-'.join(k.split('-')[:2])+'-+0';A=np.array(names[k0]['native_angle']['actor_foot'])
 assert np.array_equal(A,np.array(w['common_axial_foot_xyz'])) and np.array_equal(A-S,np.array(w['translation_to_same_xyz_as_actual_axial_foot']))
 c=libs['run'](libs['tr'](P/'native'/(k+'.json'))+(A-S))[0]
 assert c==w['strict_pairs_at_unchanged_axial_foot'] and c>0
 same[k]={'translated_to_axial_common_xyz':A.tolist(),'strict_pair_count':c,'analytic':True}
# Independently reconstruct support polytope via intersection of every pair
# of support lines, retaining points satisfying all half-space constraints.
a=np.deg2rad(np.arange(72)*5)
axis=np.column_stack([np.cos(a),np.sin(a)]); step=.02
radii=np.full(104,-np.inf); slabs=.02*np.arange(-4,100)
for k in ids:
 f=np.array(names[k]['native_angle']['actor_foot'])[[0,2]];A=libs['tr'](P/'native'/(k+'.json'))
 q=np.linalg.norm(A[:,:,[0,2]]-f,axis=-1).max(axis=1); lo,hi=A[:,:,1].min(axis=1),A[:,:,1].max(axis=1)
 overlap=(lo[None,:]<=slabs[:,None]+step)&(hi[None,:]>=slabs[:,None])
 radii=np.maximum(radii,np.max(np.where(overlap,q[None,:],-np.inf),axis=1))
dr=(D[:,:,[0,2]].reshape(-1,2)@axis.T).reshape(-1,3,72).max(1)
u,v=D[:,:,1].min(1),D[:,:,1].max(1)
DS=np.full(72,-np.inf)
for y,z in zip(slabs,radii):
    if not np.isfinite(z): continue
    idx=(u<=y+step)&(v>=y)
    if idx.any():DS=np.maximum(DS,dr[idx].max(0)+z+.01)
assert np.max(np.abs(DS-np.array(R['support_contour']['max_outward_support_m'])))<1e-12
P2=[]
for i in range(72):
 for j in range(i+1,72):
  M=axis[[i,j]]
  if abs(np.linalg.det(M))<1e-9:continue
  x=np.linalg.solve(M,DS[[i,j]])
  if np.max(axis@x-DS)<1e-11:P2.append(x)
V=np.asarray(P2)
assert np.allclose([V[:,0].min(),V[:,0].max()],R['support_contour']['lateral_extent'],rtol=0,atol=1e-12)
assert np.allclose([V[:,1].min(),V[:,1].max()],R['support_contour']['normal_line_extent_for_minmax_z'],rtol=0,atol=1e-12)
def bound(x):
    E=DS-x*axis[:,0]
    return [float(max(E[axis[:,1]<-1e-9]/axis[axis[:,1]<-1e-9,1])),float(min(E[axis[:,1]>1e-9]/axis[axis[:,1]>1e-9,1]))]
atx0=bound(0); seam={str(x):bound(x) for x in (-1.825,1.825)}
for k,v in seam.items(): assert np.allclose(v,R['support_contour']['envelope_z_at_old_seams'][k],rtol=0,atol=2e-12)
print(json.dumps({'scope':'static local CPU geometry, no ongoing controller or vision gate','native_movement_checks_from_frozen_log':181,'measured':data,'same_foot_analytic_control':same,'sampled_yaw_support':{'x_extent':[float(V[:,0].min()),float(V[:,0].max())],'z_extent':[float(V[:,1].min()),float(V[:,1].max())],'x0_z_interval':atx0,'seam_z_intervals':seam,'outward_setback_mm_to_sample_bound_only':[1000*(atx0[1]-1.35),1000*(-atx0[0]-1.45)],'not_implemented_collider':True}},indent=2))
