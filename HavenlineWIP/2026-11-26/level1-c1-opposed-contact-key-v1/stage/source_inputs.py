"""Pinned offline translation of the admitted Level 1 terrain and framing source."""
import hashlib,json,math,re,sys,os
from pathlib import Path
from functools import lru_cache
import numpy as np
parser = Path(os.environ['HAVENLINE_ARCHIVED_GLB_PARSER']).resolve()
assert hashlib.sha256(parser.read_bytes()).hexdigest() == '9ec09dcc6dedd4e9a978dc489cb1ad036f5e82dcc3ecb64046417275fa567d4b'
sys.path.insert(0,str(parser.parent))
from inspect_source import load

STOCK=Path(os.environ['HAVENLINE_PROJECT']).resolve()
FRESH=Path(os.environ['HAVENLINE_RIG']).resolve()
HASHES={'rig.LOCAL.json':'ce9551d2f34a90c9f5b1dd08c7854ecf471e8ba5965f3be99a41dfd6bb15943c',
        'skin.LOCAL.npz':'b22a32e9d0ebb28b626c757364c34a4bd00b326a5aac435c0f96ba8aae388220'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clamp(v,a,b):return min(max(v,a),b)
def sm(lo,hi,x):
 t=clamp((x-lo)/(hi-lo),0.,1.);return t*t*(3.-2.*t)
def f32(v):return float(np.float32(v))
def norm(v):return np.asarray(v)/np.linalg.norm(v)
A=[(-31,-8.6),(-24,-7.2),(-17,-9),(-10,-6.8),(-3,-8.7),(4,-6.9),(11,-8.5),(19,-6.7),(25,-8.1),(31,-7.3)]
A=np.asarray(A,np.float32).astype(float)
WIDTHS=[3.6,4.05,4.2,4.25,4.,4.25,4.,4.25,3.8,3.6]

def river(x,z):
 def s(i):
  a=A[max(0,i-1)];b=A[min(len(A)-1,i+1)]
  return float((b[1]-a[1])/(b[0]-a[0]))
 def frame(x):
  i=min(np.searchsorted(A[1:,0],x),len(A)-2)
  a,b=A[i:i+2]; h=b[0]-a[0];t=clamp((x-a[0])/h,0.,1.);t2=t*t;t3=t*t2
  m0,m1=s(i),s(i+1)
  cz=(2*t3-3*t2+1)*a[1]+(t3-2*t2+t)*h*m0+(-2*t3+3*t2)*b[1]+(t3-t2)*h*m1
  slope=((6*t2-6*t)*a[1]+(3*t2-4*t+1)*h*m0+(-6*t2+6*t)*b[1]+(3*t2-2*t)*h*m1)/h
  return np.array([x,cz],np.float32).astype(float),norm([1.,slope]),WIDTHS[i]+(WIDTHS[i+1]-WIDTHS[i])*sm(0.,1.,t)
 p=np.array([x,z]);tx=clamp(x,-31.,31.)
 for _ in range(4):
  center,tangent,_=frame(tx);tx=clamp(tx+((p-center)@tangent)*tangent[0],-31.,31.)
 center,tang,w=frame(tx)
 side=float((p-center)@np.array([-tang[1],tang[0]]))
 return abs(side)-w*.5,side

@lru_cache(maxsize=None)
def vertex(x,z):
 shore,side=river(x,z)
 # For the entire footprint the exact source lerp selects 100% snow;
 # this eliminates river scalar-roundoff from the height calculation.
 assert shore>1.45 and side>0
 xz=np.array([x,z],np.float32)
 ripple=math.sin(x*.53+math.sin(z*.26))*math.cos(z*.48)*.055
 edge=sm(13.5,24.,max(abs(x),abs(z)*.86))
 drift=edge*(.64+.52*math.sin(x*.19+z*.15)**2)
 local=0.
 for bx,bz,amp,r in np.asarray([[-8.5,8,.34,2.4],[8.4,8,.37,2.2],[-11,-1,.28,2.2],[11,-7,.44,2.7],[-3,13,.31,2.1],[-4.8,8.5,.38,1.9],[10.7,2,.43,2],[4.8,-8.4,.38,2.1],[-10,4.5,.40,2.2]],np.float32):
  q=(xz-np.array([bx,bz],np.float32))/r
  local+=float(amp)*math.exp(-float(q@q)*.5)
 path=100.0
 origin=np.array([0.,.2],np.float32)
 for dest in np.asarray([[0,12.2],[-6.6,-3.65],[6.6,-3.65],[0,-10.7],[-2.8,2.25]],np.float32):
  d=dest-origin
  near=origin+d*np.float32(clamp(float((xz-origin)@d)/float(d@d),0.,1.))
  path=min(path,float(np.linalg.norm(xz-near)))
 shoulders=(.052*math.exp(-((path-.85)/.30)**2)-.055*math.exp(-(path/.48)**2))*sm(2.,5.,float(np.linalg.norm(xz)))
 base=-.035+ripple+drift+local+shoulders
 q=np.abs(xz-np.array([0.,2.8],np.float32))-np.array([9.75,4.3],np.float32)+np.float32(.78)
 wd=float(np.linalg.norm(np.maximum(q,0)))+min(max(q),0.)-.78
 floor=.008*math.sin(x*.22)*math.sin(z*.26)
 mix=sm(-.12,1.8,wd)
 y=f32(floor+(base-floor)*mix+.12*math.exp(-((wd-.36)/.62)**2))
 return y,shore

def ground(x,z,ingredients=False):
 # Grid vertices match Surface._ensure_heights' Float32 storage.
 x0=math.floor(x*4.)*.25;z0=math.floor(z*4.)*.25
 p=np.array([(x0,z0),(x0+.25,z0),(x0,z0+.25),(x0+.25,z0+.25)])
 h=tuple(vertex(*q)[0] for q in p);u0=(x-x0)*4.;v0=(z-z0)*4.
 weight=np.array([1.-u0-v0,u0,v0,0.]) if u0+v0<=1. else np.array([0.,1.-v0,1.-u0,u0+v0-1.])
 assert np.all(weight>=-1e-13) and abs(weight.sum()-1.)<1e-13
 assert np.max(np.abs(weight@p-np.array([x,z])))<1e-13
 y=float(weight@h)
 # Return actual chosen grid triangle and barycentric weights for custody.
 if ingredients:return y,dict(xz=p.tolist(),heights=h,weights=weight.tolist(),min_grid_shore_m=min(vertex(*q)[1] for q in p))
 return y

def sources():
 for line in Path('SOURCE-SHA256SUMS').read_text().splitlines():
  h,p=line.split();assert sha(STOCK/p)==h
 assert all(sha(FRESH/n)==h for n,h in HASHES.items())
 scene=(STOCK/'previews/integrated_opening.gd').read_text()
 assert all(x in scene for x in ['Vector2(-3.25, 5.80)','camera.size = 13.0','Vector3(7, 11, 11)','camera.look_at(actor.position)'])
 layout=json.loads((STOCK/'layout.json').read_text()); XZ=np.array(layout['start_xz'],np.float32)+np.array([-3.25,5.80],np.float32)
 start=np.array([XZ[0],f32(ground(*XZ)),XZ[1]],float)
 meta,V,_,_,_,_,F=load(STOCK/'assets/characters/Character1.glb')
 # Source node chain gives no rotation or nonuniform scale between scene root
 # and mesh. Stock opening.gd then centers aggregate bound and scales to 1.75 m.
 top=meta['nodes'][meta['scenes'][0]['nodes'][0]]
 leaf=meta['nodes'][next(k for k in top['children'] if 'mesh' in meta['nodes'][k])]
 for a in (top,leaf):
  assert not any(x in a for x in ['matrix','rotation','scale'])
 src_offset=np.array(top.get('translation',[0,0,0]))+np.array(leaf.get('translation',[0,0,0]))
 b0=V.min(0)+src_offset;b1=V.max(0)+src_offset
 assert not any(x in meta['nodes'][k] for k in top['children'] if k!=next(i for i in top['children'] if 'mesh' in meta['nodes'][i]) for x in ['mesh'])
 s=float(layout['actor_height'])/(b1-b0)[1]
 # Whether the importer retains the GLTF root translation as a node or folds
 # it into the static mesh transform, min/center fit cancels that translation.
 off=s*(src_offset-np.array([(b0[0]+b1[0])*.5,b0[1],(b0[2]+b1[2])*.5]))
 world=start+off
 back=norm([7.,11.,11.]);right=norm(np.cross([0.,1.,0.],back)); up=np.cross(back,right)
 cam=np.stack((right,up,back))
 assert np.max(np.abs(cam@cam.T-np.eye(3)))<1e-12
 return start,world,s,start+np.array([7.,11.,11.]),cam,V,F
