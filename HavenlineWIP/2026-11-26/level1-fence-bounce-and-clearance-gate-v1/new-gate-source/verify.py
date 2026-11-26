from pathlib import Path
import numpy as np,sys,json,math,hashlib
src,critic,readout=map(Path,sys.argv[1:4])
this=Path(__file__).resolve().parent
sys.argv=[sys.argv[0],str(src)]
env={};exec((critic/'triangles.py').read_text().split("results={}")[0],env)
G,H=env['post'],np.array(env['pm'])
terrain=json.loads((critic/'result.json').read_text())['results']
result={}
def clip(poly,i,c,sgn):
 if not len(poly):return []
 dst=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  da,db=(a[i]-c)*sgn,(b[i]-c)*sgn
  if da<=0:dst.append(a)
  if da*db<0: dst.append(a+(b-a)*da/(da-db))
 return np.asarray(dst)
def pairs(T,G):
 low,hi=T.min(1),T.max(1);lo,H=G.min(1),G.max(1)
 N,K=env['norms'](T),env['norms'](G)
 bs=np.argwhere(np.all((hi[:,None,:]>=lo[None,:,:]-2e-7)&(H[None,:,:]>=low[:,None,:]-2e-7),axis=-1))
 vals=[(env['span'](T[i],G[j],N[i],K[j]),int(i),int(j)) for i,j in bs]
 return [q for q in vals if q[0]>4e-7]
def tagged(path):
 T,_=env['obj'](path)
 g=[];name=''
 for l in path.read_text().splitlines():
  if l.startswith('g '):name=l.split()[1]
  if l.startswith('f '):g.extend([name]*(len(l.split())-3))
 assert len(g)==len(T)
 return T,np.array(g)
for gate,v in terrain.items():
 s=1 if gate.endswith('left') else -1; fname='GateLeaf.obj' if s==1 else 'GateLeaf_Right.obj'
 T,N=tagged(this/'donor'/fname);U=T*np.array([s,1,1])
 signed=G*np.array([s,1,1])+np.array([-.19616,v['post_minus_hinge_height_m'],0])
 assert U[:,:,0].min()>0
 out={}
 for mat in sorted(set(H)):
  m=signed[H==mat].reshape(-1,3);L=m.min(0);J=m.max(0)
  reach=max(abs(L[2]),abs(J[2]))+.002
  idx=np.flatnonzero((U[:,:,1].min(1)<=J[1]+.002)&(U[:,:,1].max(1)>=L[1]-.002)&(U[:,:,0].min(1)<=reach))
  violations=[]
  minimum=1.
  for i in idx:
   p=clip(U[i],1,L[1]-.002,-1);p=clip(p,1,J[1]+.002,1);p=clip(p,0,reach,1)
   if len(p):
    rem=float(p[:,2].min()-J[0]); minimum=min(minimum,rem)
    if rem<.002-1e-7:violations.append([int(i),N[i],rem])
  out[mat]={'clipped_triangles_considered':len(idx),'y_window_m':[float(L[1]),float(J[1])],'smallest_x_margin_m':minimum if len(idx) else None,'failed_triangles':violations}
 sweep={}
 g=G+np.array([-s*.19616,v['post_minus_hinge_height_m'],0])
 for a in sorted(set([0.,15.,22.5,45.,67.5,87.85352859,90.]+[min(math.pi/2,i*2.3/60)*180/math.pi for i in range(1,42)])):
  c,z=math.cos(math.radians(a)),s*math.sin(math.radians(a))
  moved=T@np.array([[c,0,-z],[0,1,0],[z,0,c]])
  r=pairs(moved,g)
  sweep[str(a)]={'strict_pairs':len(r),'longest':max(r)[0] if r else 0}
 if gate.startswith('south'):
  attach={}
  for a,b in [('inward_hinge_stile','outward_hinge_stile'),('inward_hinge_strap_0','carved_board_1'),('inward_hinge_strap_0','carved_board_2'),('inward_hinge_strap_1','carved_board_1'),('inward_hinge_strap_1','carved_board_2'),('rear_beveled_wood_saddle','carved_board_1'),('rear_beveled_wood_saddle','carved_board_2'),('inward_hinge_rope_0','rear_beveled_wood_saddle'),('inward_hinge_rope_1','rear_beveled_wood_saddle')]:
   hit=pairs(T[N==a],T[N==b]);attach[a+' -> '+b]=len(hit)
 else:attach={}
 result[gate]={'continuous_2mm_tests':out,'strict_sweep':sweep,'attachment_crossings':attach}
print(json.dumps(result,indent=2))
