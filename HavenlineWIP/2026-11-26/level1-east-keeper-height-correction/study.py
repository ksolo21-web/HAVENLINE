from pathlib import Path
from hashlib import sha256
from collections import Counter
import json,re,math
import numpy as np
P=Path(__file__).resolve().parent
B=P.parent/'hvn-l1-owner-gate-33035-v4-native-preflight-v1'
C=B/'graphics-evidence.cklm7tMU'
A=B/'staged/HavenlineLevel1/previews/clearance_gate/owner_assets'
def sha(p):return sha256(p.read_bytes()).hexdigest()
assert sha(B/'SHA256SUMS')=='54aa0c9d591a174d4c790825ee4f90216d3ab611c8b35f3ea964683d62939314'
assert sha(C/'paid-first-frame.png')=='d5c5055af8a02d6d67fcd82110f408ae2af3b3e4a12b4eade41bcbbcba2fb4ca'
for name,d in [('33035.png','bd17e02a2999294e032d78ee93b61228658fae060da77c241934bd3fad0a01a8'),('33039.png','85712d3260ab7be14f40cd0371fa48703b74c99000e7cf25c3d3e30dd79e7548'),('33040.png','7e86d259cf4cf67d3a795ab0bb150d8ce67af7a03a23c240a8dd0e0cec137bdd')]:
 assert sha(P.parent/'hvn-owner-fence-33036-33035'/name)==d
log=(C/'write.log').read_text()
r=[json.loads(s) for s in re.findall(r'^OWNER33035_DRAW_BOUND (.+)$',log,re.M) if '"phase":"paid-first-frame"' in s]
assert len(r)==1
row=r[0]['gates']['gate-east'];assert row['angle']==0
l,rr=(side['pivot_world_origin'] for side in row['mounts'])
raise_y=round(l[1]-rr[1],7)
assert .069<raise_y<.070
base=A/'GateLeaf_Right.obj'; out=P/'candidate/GateLeaf_Right_EastAligned.obj'
src=base.read_text().splitlines()
dst=[];g=None; changed=[]
for i,line in enumerate(src):
 if line.startswith('g '):g=line[2:]
 if line.startswith('o '):line='o GateLeaf_Right_EastAligned'
 if line.startswith('v ') and g=='front_receiver_keeper':
  p=line.split(); p[2]=f'{float(p[2])+raise_y:.7f}'
  changed.append(i); line=' '.join(p)
 dst.append(line)
out.write_text('\n'.join(dst)+'\n')
(P/'candidate/owner33035.mtl').write_bytes((A/'owner33035.mtl').read_bytes())
def parse(rows):
 vs=[]; fs={}; nm=[]
 for s in rows:
  k=s.split()
  if k[0]=='g':g=k[1];fs[g]=[]
  elif k[0]=='v':vs.append([float(v) for v in k[1:]]);nm.append(g)
  elif k[0]=='f':fs[g].append([int(v)-1 for v in k[1:]])
 return np.array(vs),fs,nm
v,old,groups=parse(src);w,new,ng=parse(dst)
assert old==new and groups==ng
target='front_receiver_keeper'
indices=[i for i,g in enumerate(groups) if g==target]
assert len(indices)==80 and len(changed)==80
assert np.array_equal(w[~np.isin(np.arange(len(v)),indices)],v[~np.isin(np.arange(len(v)),indices)])
assert np.array_equal(w[:,[0,2]],v[:,[0,2]])
assert np.allclose(w[indices,1]-v[indices,1],raise_y,atol=1e-8)
assert np.array_equal(w.min(0),v.min(0)) and np.array_equal(w.max(0),v.max(0))
edges=Counter((min(a,b),max(a,b)) for face in new[target] for a,b in zip(face,face[1:]+face[:1]))
assert set(edges.values())=={2}
# Actual fixed-post continuous clearance reason: keeper inward hinge-local x>1.095m
# exceeds any post's possible cross-depth (0.159m). If a moving front point
# ever rotates into the fixed-post x<0 side, |rotated z|>=|x|, excluding all original posts.
assert min(-w[i][0] for i in indices)>1.09
assert max(abs(w[i][2]) for i in indices)<=.069
# Seat in original closed component, not a bounding-box guess.
def inside(p,tri):
 d=np.array([.337,.491,.661]); e=tri[:,1]-tri[:,0]; f=tri[:,2]-tri[:,0]
 h=np.cross(d,f); den=np.einsum('ij,ij->i',e,h); valid=np.abs(den)>1e-12
 e,f,h,den=e[valid],f[valid],h[valid],den[valid];o=np.array(p)-tri[valid,0]
 u=np.einsum('ij,ij->i',o,h)/den;q=np.cross(o,e);z=q@d/den;k=np.einsum('ij,ij->i',f,q)/den
 return (np.count_nonzero((u>1e-9)&(z>1e-9)&(u+z<1-1e-9)&(k>1e-9))%2)==1
for dy in [-.014,0,.014]:
 sample=[-1.135,.681+raise_y+dy,.051]
 assert inside(sample,w[new[target]]) and inside(sample,w[new['center_stile']])
record=json.loads((P.parent/'hvn-l1-owner-gate-33035-charcoal-latch-paid-v1/graphics-evidence.SC6mjnAN/paid-only-falsifier.json').read_text())
assert record['same_roi_evidence']['v4_paid_frame_hash']==sha(C/'paid-first-frame.png')
vertical_per_m=(row['projected_hinge_verticals_px'][1][1]-row['projected_hinge_verticals_px'][1][3])/1.35
assert (px:=raise_y*vertical_per_m)>2.9
# Same gate-south donor isn't touched; its independent terrain step is explicitly separate.
south=row=r[0]['gates']['gate-south']
print(json.dumps({'source_mesh_sha256':sha(base),'candidate_mesh_sha256':sha(out),'paid_camera':sha(C/'paid-first-frame.png'),
'detached_separate_east_keeper_offset_m':raise_y,'closed_east_terrain_hinge_y_difference_m':l[1]-rr[1],
'projected_east_keeper_y_shift_px':px,'physical_xz_silhouette_identical':True,'keeper_overlap_witnesses':3,'new_projected_roi_needs_native_exact_witness':True,
'south_unchanged_and_terrain_step_not_generalizable_m':south['mounts'][0]['pivot_world_origin'][1]-south['mounts'][1]['pivot_world_origin'][1],
'no_approval':True},indent=2))
