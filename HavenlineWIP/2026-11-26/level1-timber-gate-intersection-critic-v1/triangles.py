from pathlib import Path
import numpy as np,sys,hashlib,json,re,math as m
p=Path(sys.argv[1])
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(p/'SHA256SUMS')=='66a34c258ae60d534de8569e80466055826988b7ee20291ea45d6bd1c7ce1e12'
for l in (p/'SHA256SUMS').read_text().splitlines():
 h,n=l.split(maxsplit=1);assert sha(p/n)==h
P=p/'staged/HavenlineLevel1'
def obj(f):
 vs=[];fs=[];names=[]; name=''
 for l in f.read_text().splitlines():
  s=l.split()
  if not s:continue
  if s[0]=='v':vs.append(list(map(float,s[1:4])))
  if s[0]=='usemtl':name=s[1]
  if s[0]=='f':
   inds=[int(k.split('/')[0])-1 for k in s[1:]]; assert len(inds)>=3 and min(inds)>=0
   for j in range(1,len(inds)-1):fs.append([inds[0],inds[j],inds[j+1]]);names.append(name)
 return np.array(vs)[fs], names
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
A=np.array([[-31,-8.6],[-24,-7.2],[-17,-9],[-10,-6.8],[-3,-8.7],[4,-6.9],[11,-8.5],[19,-6.7],[25,-8.1],[31,-7.3]],float)
W=[3.6,4.05,4.20,4.25,4,4.25,4,4.25,3.80,3.60]
def center(x):
 x=float(np.clip(x,-31,31)); i=int(np.clip(np.searchsorted(A[:,0],x)-1,0,8)); a,b=A[i:i+2]; h=b[0]-a[0];t=(x-a[0])/h
 slope=lambda j:(A[min(j+1,9),1]-A[max(j-1,0),1])/(A[min(j+1,9),0]-A[max(j-1,0),0])
 j,k=slope(i),slope(i+1)
 mid=np.array([x,(2*t**3-3*t*t+1)*a[1]+(t**3-2*t*t+t)*h*j+(-2*t**3+3*t*t)*b[1]+(t**3-t*t)*h*k])
 der=((6*t*t-6*t)*a[1]+(3*t*t-4*t+1)*h*j+(-6*t*t+6*t)*b[1]+(3*t*t-2*t)*h*k)/h
 tan=np.array([1,der]);tan/=np.linalg.norm(tan)
 return mid,tan,W[i]+(W[i+1]-W[i])*smooth(0,1,t)
def shore(p):
 x=p[0]
 for _ in range(4):
  mid,t,_=center(x);x=np.clip(x+(p-mid)@t*t[0],-31,31)
 mid,t,w=center(x);return abs((p-mid)@np.array([-t[1],t[0]]))-.5*w
# Read authored exact drift tuples rather than carrying duplicated constants.
terrain=(P/'accepted_t02_surface.gd').read_text()
banks=[tuple(map(float,s.split(","))) for s in re.findall(r"Vector4\(([^)]+)\)",re.search(r"for bank in \[(.*?)\]:",terrain)[1])]
def grid(x,z):
 p=np.array([x,z]); q=np.abs(p-[0,2.8])-[9.75,4.3]+.78
 wd=np.linalg.norm(np.maximum(q,0))+min(max(q),0)-.78
 path=100
 ends=[np.array(tuple(map(float,t.split(',')))) for t in re.findall(r'Vector2\(([^)]+)\)',re.search(r'for endpoint in \[(.*?)\]:',terrain)[1])]
 for e in ends:
  origin=np.array([0,.2]);v=e-origin; near=origin+v*np.clip((p-origin)@v/(v@v),0,1)
  path=min(path,float(np.linalg.norm(p-near)))
 original=-.035+m.sin(x*.53+m.sin(z*.26))*m.cos(z*.48)*.055 + smooth(13.5,24,max(abs(x),abs(z)*.86))*(.64+.52*m.sin(x*.19+z*.15)**2)+sum(h*m.exp(-((x-a)**2+(z-b)**2)/(2*s*s)) for a,b,h,s in banks)+(.052*m.exp(-((path-.85)/.30)**2)-.055*m.exp(-(path/.48)**2))*smooth(2,5,np.linalg.norm(p))
 floor=.008*m.sin(x*.22)*m.sin(z*.26)
 assert shore(p)>1.45
 return float(np.float32(floor+(original-floor)*smooth(-.12,1.8,wd)+.12*m.exp(-((wd-.36)/.62)**2)))
def height(p):
 g=np.floor(p*4)/4;u,v=(p-g)*4;x,z=g
 a,b,c,d=grid(x,z),grid(x+.25,z),grid(x,z+.25),grid(x+.25,z+.25)
 return a+(b-a)*u+(c-a)*v if u+v<=1 else d+(b-d)*(1-v)+(c-d)*(1-u)
def section(a,d):
 t=[v for v,s in zip(a,d) if abs(s)<=2e-7]
 for j,k in ((0,1),(1,2),(2,0)):
  if min(abs(d[j]),abs(d[k]))>2e-7 and d[j]*d[k]<0:t.append(a[j]+(a[k]-a[j])*d[j]/(d[j]-d[k]))
 return np.array(t)
def norms(t):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);s=np.linalg.norm(n,axis=1);return n/np.maximum(s[:,None],1e-19)
def span(a,b,n,k):
 d=(a-b[0])@k;e=(b-a[0])@n
 if not(d.min()<-2e-7 and d.max()>2e-7 and e.min()<-2e-7 and e.max()>2e-7):return 0.
 v=np.cross(n,k);r=np.linalg.norm(v)
 if r<1e-8:return 0.
 v/=r
 x=section(a,d)@v;y=section(b,e)@v
 return max(0.,min(x.max(),y.max())-max(x.min(),y.min()))
post,pm=obj(P/'previews/r17_fence/assets/gate_post.obj')
assert len(post)==176
post*=np.array([1.12,1.14,1.12])
results={}
for gate,cen,axis in [('south',[-3.25,9.8],[1,0]),('east',[1.75,5.8],[0,-1])]:
 axis=np.array(axis);cross=np.array([-axis[1],axis[0]])
 for side,f in [(-1,'GateLeaf.obj'),(1,'GateLeaf_Right.obj')]:
  leaf,lm=obj(p/'donor'/f);assert len(leaf)==1360
  gh=np.array(cen)+axis*(side*1.20)
  pc=gh+axis*(side*.19616)
  y=min(height(pc+axis*x+cross*z) for x in np.linspace(-.18816,.18816,17) for z in [-.19309,0,.19309])-.04-height(gh)
  assert abs(y)<.15
  G=post+np.array([side*.19616,y,0]);K=norms(G);Glo,Ghi=G.min(1),G.max(1)
  samples={}
  for a in [0.,15.,22.5,45.,67.5,90.]+[min(m.pi/2,i*2.3/60)*180/m.pi for i in range(1,42)]:
   yv=-side*m.radians(a);c,s=m.cos(yv),m.sin(yv);T=leaf@np.array([[c,0,-s],[0,1,0],[s,0,c]])
   N=norms(T); lo,hi=T.min(1),T.max(1)
   bs=np.argwhere(np.all((Ghi[None,:,:]>=lo[:,None,:]-2e-7)&(hi[:,None,:]>=Glo[None,:,:]-2e-7),axis=-1))
   h=[(span(T[i],G[j],N[i],K[j]),int(i),int(j)) for i,j in bs]
   h=[q for q in h if q[0]>4e-7]
   if h:
    w=max(h);samples[f'{a:.8f}']={'pairs':len(h),'longest_segment_m':w[0],'leaf_triangle':w[1],'post_triangle':w[2],'leaf_mat':lm[w[1]],'post_mat':pm[w[2]]}
  results[gate+('-left' if side<0 else '-right')]={'post_minus_hinge_height_m':y,'intersecting_samples':samples}
print(json.dumps(dict(source=sha(p/'SHA256SUMS'),test='exact source triangulation and offline terrain/placement reconstruction; nominal sample sequence, not actual in-engine import/run',results=results),indent=2))
