"""Offline one-bit bark classifier. Uses original verifier, never invokes renderer."""
from pathlib import Path
import contextlib,io,shutil,tempfile
from scipy.ndimage import binary_dilation
HERE=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
 exec((HERE/'verify.py').read_text().split('by={}')[0])
Q0=P/'hvn-l1-crown-shadow-cause-stage-v1'
old=Q0/'graphics-evidence.8dTM6aEs'
bplan=P/'hvn-l1-crown-bark-only-proposal-v1'
assert sha(bplan/'SHA256SUMS')=='ebef9c25f21418ebd0c3fc69093b00bd939dcebbfc339e8f076d9afdf7fba270'
assert sha(Q0/'SHA256SUMS')=='b5aa7272a869dfdef789fdb60474dccf342976f5a7f6187747aa19081b40ff90'
assert sha(old/'shadow-causality-result.json')=='028b2cc7436d30ca969d062e197713a39e399139fff4fd859538be9286cc7ec2'
for path,h in {'a1':'ecd169066795663cf72530076471b0c61025a13bf7df8e2235a8f7ef4f702a64','a2':'ecd169066795663cf72530076471b0c61025a13bf7df8e2235a8f7ef4f702a64','cast_off':'0d460fab173f16cf883c2fe8e3bafb663606561e90064572d066e67d2e12846e'}.items():
 assert sha(old/path/'passive.log')==h
assert all((HERE/f).read_bytes()==(Q0/f).read_bytes() for f in ('verify.py','route_verify.py','material-diagnosis.json'))
def use_checker(a,b):
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'no_crown').symlink_to(a.resolve(),target_is_directory=True);(p/'virtual_crown').symlink_to(b.resolve(),target_is_directory=True)
  return json.loads(subprocess.check_output([sys.executable,'-B',HERE/'verify.py',p]))
old_off,=load(old/'cast_off/passive.log','CARRY_APPEARANCE')
def image(folder,t):
 a=np.asarray(Image.open(folder/f'frame-{t}.png').convert('RGBA'),dtype=np.int16)
 assert a.shape==(720,1280,4)
 return a
def stamp(rows):return [{k:v for k,v in r.items() if k not in {'scenario','rid','source_mesh_rid'}} for r in rows]
if sys.argv[1]=='--check-only':
 for a in ('a1','a2'):
  assert len(use_checker(old/a,old/'cast_off')['rows'])==3
 print(json.dumps(dict(source_only=True,stock_cast_off_historical_original_checker_pass_twice=True,renderer_run=False)))
 sys.exit(0)
def record(d,case):
 log=d/'passive.log'; w,=load(log,'CARRY_APPEARANCE'); b,=load(log,'CROWN_BARK_TREATMENT'); c,=load(log,'CROWN_CAST_TREATMENT')
 assert w['mode']=='virtual_crown' and c['case']=='off' and c['owned_cast_reset_before_free'] and c['source_original_untouched']
 assert b['case']==case and b['surface']==0 and b['end_grain_override'] is False and b['closed_owned_surface_override']==(case=='one_flag')
 assert [m['tick'] for m in b['frames']]==ids
 for br,ca,ww in zip(b['frames'],c['frames'],w['frames'],strict=True):
  assert all(br[k]==ca[k]==ww[k] for k in ('tick','physics','process')) and br['owned_rid']==ca['owned_rid']==ww['rid']>0
  assert ca['requested_cast_enum']==0 and ca['stock_crown_cast_enum']==1 and br['owned_cast_off']
  assert br['original_bark_color_off'] and br['original_amber_color_on'] and br['expected_local_replacement']==(case=='one_flag')
  assert br['stored_delta']==(['vertex_color_use_as_albedo'] if case=='one_flag' else [])
 assert stamp(w['frames'])==stamp(old_off['frames']) and w['stock_material_fingerprints']==old_off['stock_material_fingerprints']
 for a in ('a1','a2'):
  assert len(use_checker(old/a,d)['rows'])==3
 return w['frames']
stock=record(D/'stock','stock'); tint=record(D/'one_flag','one_flag')
assert stamp(stock)==stamp(tint)
for t in ids:
 assert np.max(np.abs(image(D/'stock',t)-image(old/'cast_off',t)))<=1, ('stock cast-off no longer repeatable',t)
# Exact source bark geometry only. Depth-independent silhouette is a conservative
# OUTER permission mask, not a claim of visible pixel ownership.
g=GLB(G); node=next(x for x in g.j['nodes'] if x['name']=='Pickup LOD - Crown log')
parts=[]
for p in g.j['meshes'][node['mesh']]['primitives']:
 xyz=g.read(p['attributes']['POSITION']).astype(float)
 ix=g.read(p['indices']).reshape(-1,3)
 parts.append(xyz[ix])
assert [len(x) for x in parts]==[1087,213]
def mask(T):
 out=np.zeros((720,1280),bool)
 for q in T:
  low=np.maximum(0,np.floor(q.min(axis=0)).astype(int))
  hi=np.minimum([1279,719],np.ceil(q.max(axis=0)).astype(int))
  if np.any(hi<low):continue
  X,Y=np.meshgrid(np.arange(low[0],hi[0]+1)+.5-q[0,0],np.arange(low[1],hi[1]+1)+.5-q[0,1])
  x,y=q[1:]-q[0];f=np.linalg.det(np.stack([x,y]))
  if abs(f)<1e-10:continue
  u=(X*y[1]-Y*y[0])/f;v=(x[0]*Y-x[1]*X)/f
  out[low[1]:hi[1]+1,low[0]:hi[0]+1]|=(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)
 return binary_dilation(out,iterations=2)
result=[]
for t,r in zip(ids,tint):
 cb,cp=tr(r['prop_submitted_transform']);kb,kp=tr(r['camera'])
 def project(x):
  p=((x@cb.T+cp-kp)@kb)[:,:,:2]
  return p*np.array([720/13,-720/13])+[640,360]
 bark=mask(project(parts[0])); amber=mask(project(parts[1]))
 assert bark.any() and amber.any() and bark.sum()<.02*720*1280
 O=image(D/'stock',t); N=image(D/'one_flag',t); change=N-O
 delta=np.max(abs(change),axis=2)
 assert delta[~bark].max()<=1, ('outside bark projection changed',t)
 durable=delta>=2; assert (durable & bark).any(), ('bark flag did not produce observable change on this key',t)
 assert not np.any(durable & amber & ~bark)
 rgb=N[:,:,:3][durable&bark]
 result.append(dict(tick=t,max_outside_bark_pixel_delta=int(delta[~bark].max()),
      bark_local_pixels_different=int((durable&bark).sum()),amber_only_upper_bound_untouched=True,
      local_changed_rgb_median=np.median(rgb,axis=0).tolist()))
print(json.dumps(dict(scope='bark one flag desktop appearance-only comparative evidence',
 exact_original_checker_passes_each_bark_case_against_both_historical_controls=True,
 independent_readability_still_required=True,attachment_or_carry=False,rows=result),indent=2))
