from pathlib import Path
from collections import Counter
import hashlib,json,math,numpy as np
root=Path(__file__).resolve().parent
owner=root.parent/'hvn-owner-fence-33036-33035'
pins=['bd17e02a','067b1e9f','a20a48ef','1be05c57']
for i,h in enumerate(pins):assert hashlib.sha256((owner/(str(33035+i)+'.png')).read_bytes()).hexdigest().startswith(h)
F={}; mats={}
def emit(k,m,rings):
 A=np.asarray(rings); n=A.shape[1]; fs=[]
 for aa,bb in zip(A[:-1],A[1:]):
  for i in range(n):
   j=(i+1)%n;fs.extend(((aa[i],aa[j],bb[j]),(aa[i],bb[j],bb[i])))
 for y,side in [(A[0],-1),(A[-1],1)]:
  c=y.mean(0)
  for i in range(n):fs.append((c,y[(i+1)%n],y[i]) if side==-1 else (c,y[i],y[(i+1)%n]))
 fs=np.asarray(fs)
 vol=np.einsum('ij,ij->i',fs[:,0],np.cross(fs[:,1],fs[:,2])).sum()
 assert abs(vol)>1e-9,(k,vol)
 if vol<0:fs=fs[:,::-1,:]
 F[k]=fs;mats[k]=m
def theta(n):return np.arange(n)/n*np.pi*2
def map_arm(p,which):
 return p if which==0 else np.array([-p[2],p[1],-p[0]])
def logs(name,center,rx,rz,top,which):
 angular=theta(20)
 def ring(y,k,snow):
  return [map_arm(np.array([center+rx*k*math.cos(a),y+(.006*math.cos(3*a) if snow else 0),rz*k*math.sin(a)]),which) for a in angular]
 emit(name,'timber',[ring(z,i,0) for z,i in [(-.04,.92),(-.01,1),(.81,1),(top-.20,.99),(top-.095,.60)]])
 emit(name+'_cap','snow',[ring(z,i,1) for z,i in [(top-.29,.94),(top-.235,1.02),(top-.16,1.01),(top-.085,.77),(top-.038,.47),(top-.005,.04)]])
logs('shared_corner',0,.142,.142,1.46,0)
for a in range(2):
 arm='south' if a==0 else 'west'
 logs(arm+'_middle',.293,.116,.079,1.43,a)
 logs(arm+'_outer',.552,.116,.079,1.45,a)
 for b,y in enumerate([.30,.88]):
  rail=arm+f'_rail_{b}'
  t=theta(20)
  emit(rail,'rail',[[map_arm(np.array([s,y+.061*math.cos(j),.045+.052*math.sin(j)]),a) for j in t] for s in [.095,.115,.44,.585]])
  for mode in (-1,1,0):
   name=arm+f'_rope_{b}_{mode}'
   ends=np.linspace(.095,.552,45)
   path=[]
   for x in ends:
    alpha=(x-ends[0])/(ends[-1]-ends[0]); u=min(1,alpha/.20,(1-alpha)/.20)
    ramp=u*u*(3-2*u)
    if mode:
     q=mode*.052*math.cos(math.pi*alpha)
     front=.045+.052*math.sqrt(max(.05,1-(q/.061)**2))
     angle=.003*(1-(q/.052)**2)**3*mode
     path.append(np.array([x,y+q, .043+(front-.043)*ramp+angle*ramp]))
    else:path.append(np.array([x,y+.003*math.cos(alpha*math.tau),-.045-.027*ramp]))
   rings=[]
   for i,c in enumerate(path):
    tang=path[min(i+1,len(path)-1)]-path[max(i-1,0)]
    tang/=np.linalg.norm(tang); rz=np.cross(tang,[0,1,0]);rz/=np.linalg.norm(rz)
    ry=np.cross(rz,tang)
    rings.append([map_arm(c+ry*(.015*math.cos(j))+rz*(.008*math.sin(j)),a) for j in theta(12)])
   emit(name,'hemp_light' if mode==1 else 'hemp_warm',rings)
def closed(f):
 cc=Counter()
 for row in f:
  R=[tuple(x) for x in np.round(row,8)]
  for i in range(3):cc[tuple(sorted((R[i],R[(i+1)%3])))]+=1
 return all(i==2 for i in cc.values())
assert all(closed(t) for t in F.values())
# Strict exact triangle crossing witness (no broad-phase false positives; touching and coplanar not certified).
pin=root.parent/'hvn-l1-gate-art-admission-protocol/triangles.py'
assert hashlib.sha256(pin.read_bytes()).hexdigest()=='f0dbc0fd1f1be4c9356e95835553d93bd3a506447c8f74c883837fe594b1a301'
num=pin.read_text();ns={'np':np}
exec(num[num.index('def section(a,d)'):num.index('post,pm=obj(')],ns)
norms,span=ns['norms'],ns['span']
def strict(X,Y):
 lo,hi=np.maximum(X.min((0,1)),Y.min((0,1))),np.minimum(X.max((0,1)),Y.max((0,1)))
 if np.any(hi<=lo):return (0,0)
 X=X[np.all((X.min(1)<=hi)&(X.max(1)>=lo),axis=1)]
 Y=Y[np.all((Y.min(1)<=hi)&(Y.max(1)>=lo),axis=1)]
 x0,x1=X.min(1),X.max(1);y0,y1=Y.min(1),Y.max(1)
 n,k=norms(X),norms(Y);res=[]
 for i in range(len(X)):
  for j in np.flatnonzero(np.all((x0[i]<=y1)&(y0<=x1[i]),axis=1)):
   q=span(X[i],Y[j],n[i],k[j])
   if q>4e-7:res.append(q)
 return (len(res),max(res,default=0)*1000)
checks={}
unrelated=[]
from itertools import combinations
for x,y in combinations(F,2):
 c=strict(F[x],F[y])
 if c[0]:checks[x+'/'+y]=c
 if c[0] and x.startswith('south') and y.startswith('west'):unrelated.append([x,y,c])
assert not unrelated,unrelated
for side in ('south','west'):
 for level in range(2):
  rail=side+f'_rail_{level}'
  for post in ('shared_corner',side+'_middle',side+'_outer'):
   assert strict(F[post],F[rail])[0]>0,(post,rail)
  for hand in (-1,1):
   rope=side+f'_rope_{level}_{hand}'
   assert strict(F[rail],F[rope])[0]>0
  assert strict(F[side+'_middle'],F[side+f'_rope_{level}_0'])[0]>0
# 100% inside shared timber radius on end cap ring (rails overlap corner timber intentionally).
ringmargin=.142-max(math.hypot(.095,.045+.052),math.hypot(.095,.045-.052))
assert ringmargin>.006
G=np.concatenate(list(F.values()))
assert G.min((0,1))[0]>=-.15 and G.max((0,1))[2]<=.15
pal={'timber':(.81,.43,.17),'snow':(.94,.956,.99),'rail':(.69,.34,.15),'hemp_light':(.98,.87,.63),'hemp_warm':(.93,.775,.51)}
s=['# Detached authoring fixture only. No indexed terrain or integration.','mtllib Corner.mtl','s 1']
i=1
for group,t in F.items():
 s.extend(['o '+group,'usemtl '+mats[group]])
 # Keep exact per-part averaged smooth normals rather than borrowing paid texture/normal.
 sums={}
 for tri,n in zip(t,np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])):
  for v in tri:
   k=tuple(v);sums[k]=sums.get(k,np.zeros(3))+n
 for tri in t:
  for v in tri:
   n=sums[tuple(v)];n/=max(np.linalg.norm(n),1e-20)
   s.extend(['v '+' '.join(f'{x:.9f}' for x in v),'vn '+' '.join(f'{x:.9f}' for x in n)])
  s.append('f '+' '.join(f'{j}//{j}' for j in range(i,i+3)));i+=3
out=root/'candidate';out.mkdir(exist_ok=True)
(out/'Corner.obj').write_text('\n'.join(s)+'\n')
(out/'Corner.mtl').write_text(''.join('newmtl '+k+'\nKd '+' '.join(map(str,v))+'\nPr .85\n\n' for k,v in pal.items()))
print(json.dumps(dict(status='isolated author fixture; no game placement or gate/counter change',triangles=len(G),closed_solid_groups=len(F),intersection_pairs_and_max_segment_mm=checks,side_vs_side_unintended_intersections=unrelated,
 shared_timber_one_post_one_cap=True,rail_corner_cap_radial_embed_mm=ringmargin*1000,corner_base_analytic_y_m=float(G[:,:,1].min()),bounds_m=[G.min((0,1)).tolist(),G.max((0,1)).tolist()],
 front_x_per_arm_level=1,rear_courses_per_arm_level=1,approved_reference_hash_prefixes=pins,mesh_notes='Actual opposing 3D rope lines and one rear visual course, with deliberate end/rail embed. Ends are fitted/capped within solids (not a seamless real single knot). No detached rear/front visual evidence or texture pass.'),indent=2))
