from pathlib import Path
import hashlib,re,json
from decision import controls,TAU
P=Path(__file__).resolve().parent.parent
S=P/'hvn-l1-carry-appearance-censused-v3'
D=S/'graphics-evidence.cBhGLs96'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(S/'SHA256SUMS')=='90d812449ace6af8d3e8003aa30b3f1f9b2d34ef5c57b10f5f1d7e42d3d535aa'
verify=S/'verify.py'
src=verify.read_text()
for needle in ['direct=hull_mask(project(received))','shadow=hull_mask(project(np.concatenate([received,foot])))&~direct',
               'assert np.max(delta[~(direct|shadow)])<=1','assert (changed&direct).sum()>=100',
               'assert int((direct|shadow).sum()) < .02*720*1280']:
 assert needle in src,needle
orig={}
for k in ('no_crown','virtual_crown'):
 folder=D/k;log=folder/'passive.log'
 x,=[json.loads(s) for s in re.findall(r'^CARRY_APPEARANCE (.+)$',log.read_text(),re.M)]
 assert x['mode']==k and x['rid_torn_down'] and x['renderer_object_only']
 assert [f['tick'] for f in x['frames']]==[128,129,142]
 assert [m['vertex_color_use_as_albedo'] for m in x['stock_material_fingerprints']]==[False,True]
 assert all(sha(folder/(f'frame-{t}.png'))==h for t,h in x['images'].items())
 orig[k]={'native_log_sha256':sha(log),'private_original_frame_digests':x['images']}
controls()
print(json.dumps(dict(scope='pre-registered source-only protocol; no native outcomes', original_receipts=orig,
 unchanged_checker_sha256=sha(verify),threshold_outside_max_code_unit=TAU,unchanged_roi_max_viewport_fraction=.02,unchanged_min_direct_prop_changed_px=100,
 original_independent_negative_counts_as_received=[864,85,211],original_independent_count_condition='snow-darkening pixels outside permitted region noted by prior critic, pinned here only as prior receipt value, not independently recalculated',
 labels=['A1 no instance','A2 no instance','one isolated owned Crown instance CAST_ON','identical logical owned Crown instance role CAST_OFF'],
 normalized_original_ticks=[128,129,142],bark_or_asset_change=False,renderer_run=False,device_result=False),indent=2))
