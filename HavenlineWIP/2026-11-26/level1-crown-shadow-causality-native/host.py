"""Host-only pre-registered verification. Never invokes Godot."""
from pathlib import Path
import io,contextlib,shutil,tempfile,inspect
from decision import decide,controls
# Evaluate only exact geometry/custody definitions from original immutable verifier.
HERE=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
 exec((HERE/'verify.py').read_text().split('by={}')[0])
base=P/'hvn-l1-carry-appearance-censused-v3'
old=base/'graphics-evidence.cBhGLs96'
plan=P/'hvn-l1-crown-shadow-cause-protocol-v1'
assert sha(plan/'SHA256SUMS')=='56f62816c302df8a5b1a895abcaffd56f88d42ac27d60ee8b6b1e1e7c3785f39'
assert sha(base/'SHA256SUMS')=='90d812449ace6af8d3e8003aa30b3f1f9b2d34ef5c57b10f5f1d7e42d3d535aa'
assert (HERE/'verify.py').read_bytes()==(base/'verify.py').read_bytes()
assert (HERE/'route_verify.py').read_bytes()==(base/'route_verify.py').read_bytes()
assert (HERE/'material-diagnosis.json').read_bytes()==(base/'material-diagnosis.json').read_bytes()
prior=json.loads((plan/'result.json').read_text())
for m,res in prior['original_receipts'].items():
 d=old/m
 assert sha(d/'passive.log')==res['native_log_sha256']
 assert all(sha(d/(f'frame-{t}.png'))==h for t,h in res['private_original_frame_digests'].items())
source=(HERE/'verify.py').read_text()
exec(source.split('def hull_mask')[1].split('rows=[]')[0].join(['def hull_mask','']))
mask_logic=source.split(" rb,ro=tr(B['core'])")[1].split(' I=[]')[0]
exec('def masks(B):\n rb,ro=tr(B[\'core\'])'+mask_logic+' return direct,shadow\n')
def image(folder,t):
 f=folder/f'frame-{t}.png'; raw=np.asarray(Image.open(f).convert('RGBA'),dtype=np.uint8)
 assert raw.shape==(720,1280,4)
 return raw
def receipt(d,case):
 log=d/'passive.log'
 original,=load(log,'CARRY_APPEARANCE')
 this,=load(log,'CROWN_CAST_TREATMENT')
 assert this['case']==case and this['source_original_untouched'] and this['owned_cast_reset_before_free']==(case!='none')
 assert original['mode']==('no_crown' if case=='none' else 'virtual_crown')
 f=original['frames']; fcase=this['frames']
 assert [x['tick'] for x in f]==ids and [x['tick'] for x in fcase]==ids
 assert len({x['rid'] for x in f})==1 and all((x['rid']>0)==(case!='none') for x in f)
 for z,c in zip(f,fcase):
  assert all(z[k]==c[k] for k in ('physics','process','tick'))
  assert c['owned_rid']==z['rid'] and c['stock_crown_cast_enum']==1
  assert c['requested_cast_enum']=={'none':-1,'on':1,'off':0}[case]
 for t,h in original['images'].items(): assert sha(d/(f'frame-{t}.png'))==h
 assert subprocess.check_output([sys.executable,'-B',HERE/'route_verify.py',d])==(Q/'passive-result.json').read_bytes()
 return f
def common(rows): return [{k:v for k,v in r.items() if k not in {'scenario','rid','source_mesh_rid'}} for r in rows]
def use_checker(a,b):
 with tempfile.TemporaryDirectory() as tmp:
  p=Path(tmp);(p/'no_crown').symlink_to(a.resolve(),target_is_directory=True);(p/'virtual_crown').symlink_to(b.resolve(),target_is_directory=True)
  return subprocess.run([sys.executable,'-B',HERE/'verify.py',p],capture_output=True,text=True)
old_appeared,=load(old/'virtual_crown/passive.log','CARRY_APPEARANCE')
old_frames=old_appeared['frames']
def support(a,on,U):
 diff=on.astype(np.int16)-a.astype(np.int16)
 hit=(np.max(np.abs(diff),axis=2)>1)&U
 assert hit.any() and (diff[:,:,:3][hit]<=1).all() and (diff[:,:,:3][hit]<-1).any(axis=1).all(), 'original outside signature changed sign'
 return hit
prior_masks={}
for t,r in zip(ids,old_frames):
 direct,shadow=masks(r); U=~(direct|shadow)
 oa=image(old/'no_crown',t); ob=image(old/'virtual_crown',t)
 M=support(oa,ob,U)
 prior_masks[t]=(direct,shadow,M)
assert [int(prior_masks[t][2].sum()) for t in ids]==prior['original_independent_negative_counts_as_received']
if sys.argv[1]=='--check-only':
 controls()
 check=use_checker(old/'no_crown',old/'virtual_crown')
 assert check.returncode!=0 and 'AssertionError: out-of-bounds native diff' in check.stderr
 print(json.dumps(dict(source_only=True,native_runs_started=0,source_checked_rejected_off_roi_pixels=[int(prior_masks[t][2].sum()) for t in ids],
    original_checker_expected_exact_negative=True,engine=False)))
 sys.exit(0)
aa1=receipt(D/'a1','none'); aa2=receipt(D/'a2','none')
assert common(aa1)==common(aa2)==common(old_frames), 'A/A stock pose/route/clock/camera mismatch'
for t in ids:
 delta=np.max(abs(image(D/'a1',t).astype(np.int16)-image(D/'a2',t).astype(np.int16)),axis=2)
 assert int(delta.max())<=1, ('A/A nonrepeatable',t,int(delta.max()))
if len(sys.argv)>2 and sys.argv[2]=='--aa-only':
 print(json.dumps(dict(all_three_exact_a_a_within_original_code_limit=True)))
 sys.exit(0)
onf=receipt(D/'cast_on','on');offf=receipt(D/'cast_off','off')
assert common(onf)==common(offf)==common(old_frames)
measure=[]
for t,r in zip(ids,onf):
 orig_direct,orig_shadow,orig_M=prior_masks[t]
 direct,shadow=masks(r)
 assert np.array_equal(orig_direct,direct) and np.array_equal(orig_shadow,shadow)
 U=~(direct|shadow)
 a,b,on,off=[image(D/z,t) for z in ('a1','a2','cast_on','cast_off')]
 assert np.array_equal(support(a,on,U),orig_M) and np.array_equal(support(b,on,U),orig_M), ('ON outside original pixel support did not reproduce',t)
 state=decide(a,b,on,off,direct,shadow)
 assert state=='OBSERVED_CAST_CAUSAL_AT_THIS_TICK_ONLY',(t,state)
 measure.append(dict(tick=t,originating_excluded_pixels=int(orig_M.sum()),observed_caster_attribution=state))
for reference in ('a1','a2'):
 a=D/reference
 on=use_checker(a,D/'cast_on'); off=use_checker(a,D/'cast_off')
 assert on.returncode!=0 and 'AssertionError: out-of-bounds native diff' in on.stderr, 'original ON did not reject exactly'
 assert off.returncode==0, off.stderr
print(json.dumps(dict(three_seeded_native_shadow_only_controls=measure,unchanged_original_checker_OFF_pass_twice=True,unchanged_original_checker_ON_same_reject_twice=True,
   same_RID_configuration_except_cast=True,not_runtime_art_or_device_approval=True),indent=2))
