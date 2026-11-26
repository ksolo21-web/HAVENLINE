from pathlib import Path
import hashlib,json,math,sys
import numpy as np
graft,ref=map(Path,sys.argv[1:3])
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ref/'SHA256SUMS')=='65aa400c4e8639953f29b3607ed51a40ed08312cefa50f3812165a98b5a4f3f0'
for l in (ref/'SHA256SUMS').read_text().splitlines():
 h,n=l.split(maxsplit=1);assert sha(ref/n)==h
sys.argv=[sys.argv[0],str(graft)]
e={};exec((ref/'triangles.py').read_text().split('results={}')[0],e)
prev=json.loads((ref/'result.json').read_text())
src=prev['results']
bounds={}
for name in ['timber','orange','snow']:
 g=e['post'][np.array(e['pm'])==name].reshape(-1,3)
 bounds[name]=dict(inward_limit_from_hinge=-.19616+float(g[:,0].max()),height_unseated_bounds=[float(g[:,1].min()),float(g[:,1].max())],depth_bounds=[float(g[:,2].min()),float(g[:,2].max())])
R={}
for gate in src:
 left=gate.endswith('left');sgn=1 if left else -1
 f=graft/'donor'/('GateLeaf.obj' if left else 'GateLeaf_Right.obj')
 leaf,labels=e['obj'](f)
 post=e['post']+np.array([-sgn*.19616,src[gate]['post_minus_hinge_height_m'],0.])
 samples={}
 for a in [0,22.5,45,67.5,87.85352859,90]:
  c,s=math.cos(math.radians(a)),sgn*math.sin(math.radians(a))
  moved=leaf@np.array([[c,0,-s],[0,1,0],[s,0,c]])
  n,k=e['norms'](moved),e['norms'](post)
  mx,Xx=moved.min(1),moved.max(1)
  my,Xy=post.min(1),post.max(1)
  pairs=np.argwhere(np.all((Xx[:,None,:]>=my[None,:,:]-2e-7)&(Xy[None,:,:]>=mx[:,None,:]-2e-7),axis=-1))
  solved=[]
  for i,j in pairs:
   if labels[i] not in {'board','board_warm','board_soft'}: continue
   span=e['span'](moved[i],post[j],n[i],k[j])
   if span>4e-7:solved.append((span,int(i),int(j)))
  samples[str(a)]={'board_only_strict_pairs':len(solved)}
  if solved:
   length,i,j=max(solved);samples[str(a)]['strongest']={'leaf_triangle':i,'post_triangle':j,'leaf_triangle_source_coordinates':leaf[i].tolist(),'post_triangle_seated_coordinates':post[j].tolist(),'post_material':e['pm'][j],'strict_segment_m':length}
 R[gate]=dict(donor_sha256=sha(f),samples=samples)
png=Path('havenline-ref-audit/t03-old/18591.png')
print(json.dumps(dict(critic=sha(ref/'SHA256SUMS'),graft=sha(graft/'SHA256SUMS'),approved_gate_reference='18591.png supplied by owner in ChatGPT (reference only, no OBJ picked)',local_reference_verified=png.is_file(),post_group_conservative_bounds_m=bounds,result=R),indent=2))
