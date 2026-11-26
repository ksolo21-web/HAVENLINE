"""Native-only A/B audit; no encoding, crop, motion synthesis, engine launch or score."""
from pathlib import Path
import copy,hashlib,json,re,sys,math
import numpy as np
from raw_verify import SIZES as FRAME_BYTES,verify_native_raw
D=Path(sys.argv[1])
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'hvn-l1-carry-cycle-palette-v1/graphics-evidence.WJBzcCP5/palette.json'
def sha(f):
 with f.open('rb') as q:return hashlib.file_digest(q,'sha256').hexdigest()
assert sha(BASE)=='adc3a22f4f87c4b51ad49940477e3b78a638f50fd5e6bf4c2de237a5347ac836'
old=json.loads(BASE.read_text())
HERO='95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099'
def receipt(name):
 log=(D/(name+'.log')).read_text()
 assert 'C1_NORMAL_REJECT' not in log
 s,=re.findall(r'^C1_NORMAL_RECEIPT (.+)$',log,re.M)
 return json.loads(s)
def m(t):
 v=np.eye(4);v[:3,:3]=np.array(t[1:]).T;v[:3,3]=t[0];return v
def verify_skin(out,rows,keys):
 w=json.loads((out/'palette.json').read_text())
 assert not w['gpu_vertex_readback'] and w['bindings']==old['bindings'] and len(w['bindings'])==66
 assert w['surfaces']==old['surfaces'] and len(w['surfaces'])==1 and w['surfaces'][0]['rows']==52898
 assert [r['tick'] for r in w['rows']]==keys
 def load(k,d,static=False):
  h=w['streams'][k]; path=out/k
  assert sha(path)==h['sha256'] and path.stat().st_size==h['bytes']
  if static:assert h==old['streams'][k]
  return np.fromfile(path,d)
 src=load('s0-source.f32','<f4',True).reshape(-1,3); indices=load('s0-indices.i32','<i4',True)
 J=load('s0-joints.i32','<i4',True).reshape(-1,4); wt=load('s0-weights.f32','<f4',True).reshape(-1,4)
 assert len(indices)==96001*3 and len(w['streams'])==7
 assert np.isfinite(src).all() and np.isfinite(wt).all()
 q=np.rint(wt.astype('f8')*65535).astype('i8')
 assert np.array_equal(wt,(q/65535.).astype('<f4')) and q.min()>=0 and q.max()<=65535 and q.sum(1).min()>=65531 and q.sum(1).max()<=65535
 bind=np.array([m(b['bind']) for b in w['bindings']])
 sp=next(i for i,b in enumerate(w['bindings']) if b['name']=='Spine02')
 exact=[]
 for r in w['rows']:
  t=r['tick']; row=rows[t-1]
  assert all(r[k]==row[k] for k in ('tick','draw','physics','process','clip','phase'))
  p=np.array([[m(t),m(s)] for t,s in r['pose_and_product_by_slot']])
  assert p.shape==(66,2,4,4) and np.isfinite(p).all() and np.max(abs(p[:,0]@bind-p[:,1]))<1e-5
  assert np.max(abs(p[sp,0]-m(r['spine_local'])))<1e-6 and np.max(abs(m(r['skeleton'])@p[sp,0]-m(r['spine_world'])))<1e-5
  bake=load(f'{t}-s0-baked.f32','<f4').reshape(-1,3)
  assert np.isfinite(bake).all()
  g=np.einsum('nwij,nj,nw->ni',p[:,1][J],np.c_[src,np.ones(len(src))],wt)[:,:3]
  rest=src*(1.-wt.astype('f8').sum(1,keepdims=True))
  basis=m(r['mesh'])[:3,:3]
  err=float(np.linalg.norm((g+rest-bake)@basis.T,axis=1).max())
  moved=int((np.linalg.norm((bake-src)@basis.T,axis=1)>.001).sum())
  assert err<=.00005 and moved>=1000
  exact.append(dict(tick=t,max_registered_bake_delta_m=err,rows_moving_over_one_mm=moved,shape_sha256=w['streams'][f'{t}-s0-baked.f32']['sha256']))
 assert len({x['shape_sha256'] for x in exact})>=2
 return exact
report={}
for clip,n,speed,length,bakes in [('walk',154,1.5,2.3333332538604736,[20,90,160]),('run',98,4,1.25,[20,57,93])]:
 names=[clip+'-trace-only',clip+'-native-rgb']
 a,b=map(receipt,names)
 c=copy.deepcopy(b)
 assert c.pop('rgb') is True and a.pop('rgb') is False
 rgbhash=c.pop('rgb_sha256');assert rgbhash and a.pop('rgb_sha256')==''
 fmt=c.pop('native_format'); assert fmt in FRAME_BYTES and a.pop('native_format')==''
 writer=c.pop('writer');assert a.pop('writer')=={}
 assert c==a, 'measurement changes native camera/input/pose/clock or protected state'
 assert b['image']==[1280,720] and b['kind']==clip and b['asset']==HERO and b['keys']==bakes and b['stock_ordinary_touch_only']
 assert (b['pre'],b['motion_rows'],b['post'])==(8,n,12)
 pin=b['protected']; assert pin['wood']==0 and not pin['sources'] and not pin['receipt'] and not pin['camp'] and pin['save']==[False,False] and len(pin['gates'])==2 and not any(g['open'] for g in pin['gates']) and pin['trees'][1]==0
 rows=b['rows']; assert len(rows)==8+n+12
 assert abs(b['start'][0]+3.25)<.001 and abs(b['start'][2]-11.8)<.001
 assert abs((b['end'][0]-b['start'][0])-speed*n/60)<.04
 for i,r in enumerate(rows,1):
  held=8<i<=8+n
  assert (r['tick'],r['draw'],r['floor'],r['held'],r['clip'])==(i,i,True,held,'l1_hero_preview/'+(clip if held else 'idle'))
  assert math.isfinite(r['phase']) and r['phase']>=0 and r['phase']<=r['length']+.0005
  if i>1:
   last=rows[i-2];assert r['physics']==last['physics']+1 and r['process']==last['process']+1
  assert abs(r['position'][2]-11.8)<.025 and np.isfinite(m(r['camera'])).all() and np.isfinite(m(r['actor'])).all()
  if held:
   assert r['input'][0]==17 and r['input'][1]==[450,375]
   dv=np.array(r['input'][2])-r['input'][1]
   v=np.array([11,7])/np.hypot(11,7)*(82 if clip=='run' else 30.75)
   assert np.linalg.norm(dv-v)<.0001 and abs(r['delta_xz'][0]-speed/60)<.002 and abs(r['delta_xz'][1])<.0005 and abs(r['length']-length)<.0005
  else:assert r['input'][0]==-1 and np.linalg.norm(r['delta_xz'])<.0005
 motion=rows[8:8+n]
 stable=motion[7:]
 d=np.diff([r['phase'] for r in stable]);wrap=(d<0);wrapped=np.where(wrap,d+length,d)
 assert wrap.sum()>=1 and np.max(abs(wrapped-1/60))<.0005 and sum(wrapped)>=length-.0005
 assert all(r['phase']>=.10-1e-6 or idx>=round(length*60)-7 for idx,r in enumerate(stable))
 skin0=verify_skin(D/names[0],rows,bakes);skin1=verify_skin(D/names[1],rows,bakes)
 assert skin0==skin1
 assert sha(D/names[0]/'palette.json')==sha(D/names[1]/'palette.json')
 raw=D/names[1]/'native.rgb'
 assert not (D/names[0]/'native.rgb').exists()
 hashes=verify_native_raw(raw,fmt=fmt,n=len(rows),worker=writer,expected=rgbhash)
 assert len(set(hashes[8:8+n]))>=n*.90
 report[clip]=dict(width=1280,height=720,frames=len(rows),first_last_observed_motion_draw=[9,8+n],
   settled_observed_phase_span_s=float(sum(wrapped)),nominal_period_s=length,wrapped_edges=int(wrap.sum()),
   native_rgb_sha256=rgbhash,native_format=fmt,peak_writer_slots=writer['peak'],individual_rgb_sha256=hashes,sparse_skin=skin1)
print(json.dumps(dict(captures=report,logical_simulation_hz=60,actual_device_review=False,actual_gpu_vertex_readback=False,
  axe=False,rig_quality_score=None,gate_floor_required=9.5),indent=2))
