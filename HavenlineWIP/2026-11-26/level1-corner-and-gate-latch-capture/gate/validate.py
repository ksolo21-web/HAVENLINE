from pathlib import Path
from hashlib import sha256
from PIL import Image
import json, re, sys, math
from metrics import calc,masks
h=Path(__file__).resolve().parent
control=h.parent/'hvn-l1-owner-gate-33035-v4-native-preflight-v1/graphics-evidence.cklm7tMU'
out,profile=map(Path,sys.argv[1:3])
def hash(b):return sha256(b).hexdigest()
for name,value in json.loads((h/'control-pins.json').read_text()).items():assert hash((control/name).read_bytes())==value
new=(out/'write.log').read_text();old=(control/'write.log').read_text()
bad=[s for s in new.splitlines() if re.search(r'error:|warning:|parse error|^fail|^DRAW_REJECT',s,re.I)]
assert len(bad)<=1 and all(s=='WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.' for s in bad)
assert re.search(r'^OpenGL .* - Compatibility - Using Device: Mesa - llvmpipe ',new,re.M)
def one(prefix,log):
 r=re.findall('^'+prefix+' (.+)$',log,re.M);assert len(r)==1;return r[0]
def only_paid(log):
 rows=[json.loads(s) for s in re.findall(r'^L1_POST_DRAW (.+)$',log,re.M)]
 return [x for x in rows if x['phase']=='paid-first-frame'][0]
def passes(log):
 just=log[:log.index('L1_COMBINED_CHECKPOINT {"paid":true,"phase":"paid-first-frame"')]
 return re.findall(r'^PASS (.+)$',just,re.M)
assert passes(new)==passes(old)
assert one('LATCH_PAID_ONLY_DONE',new)==f'{len(passes(old))} route checks tick=357'
assert len(re.findall(r'^L1_POST_DRAW ',new,re.M))==1
a,b=only_paid(old),only_paid(new)
for k in a.keys()-{'pixel_sha256'}:assert a[k]==b[k],k
assert b['queued']['tick']==b['draw']['tick']==357 and b['draw']['stock']==0 and b['draw']['paid']
assert [x.name for x in out.glob('*.png')]==['paid-first-frame.png']
with Image.open(out/'paid-first-frame.png') as im:
 assert im.size==(1280,720) and b['pixel_sha256'] in {hash(im.convert(mode).tobytes()) for mode in ('RGB','RGBA')}
def owner(log):
 rows=[json.loads(s) for s in re.findall(r'^OWNER33035_DRAW_BOUND (.+)$',log,re.M)]
 return [x for x in rows if x['phase']=='paid-first-frame'][0]
ref=owner(old);got=owner(new)
cfg=json.loads((h/'staged/HavenlineLevel1/previews/clearance_gate/owner_runtime_census.json').read_text())['meshes']
n=0; unchanged=0
for gate in got['gates'].values():
 for p in gate['mounts']+gate['stationary_owner_posts']:
    src=Path(p['source']).name
    slots=p['effective_finish']['slots']
    assert len(slots)==len(cfg[src]['surfaces'])
    for slot,surface in zip(slots,cfg[src]['surfaces']):
      g=surface['source_group']
      role=slot.pop('front_latch_role')
      expected={'front_handle_rosette':1,'front_handle_owned_bar':2,'front_receiver_keeper':1}.get(g,0)
      assert type(role) is int and role==expected
      n+=(role!=0)
      unchanged+=(role==0)
assert (n,unchanged)==(6,120) and got==ref
assert masks(out)==masks(control)
save=json.loads((profile/'opening-v3.json').read_text())
payload=save['payload'];assert save['version']==1 and save['sha256']==hash(payload.encode())
state=json.loads(payload);assert state['version']==1 and state['stock']=={'wood':0}
assert state['receipt']=={'offer':'center-hearth','grant':'center-hearth','typed_debit':{'wood':3},'revision':1}
from roi import compare
regional=compare(h,control,out,ref)
print(json.dumps({'scope':'One ordinary paid native stock camera frame; no 78/16 rerun or approval',
 'route_prefix_checks':len(passes(new)),'tick':357,'same_prior_mesh_mounts_and_effective_palette':126,'front_charcoal_satin_roles':n,'unchanged_surface_defaults':unchanged,
 'v4':calc(control,masks(control)),'latch':calc(out,masks(out)),'same_profile_ledger_v1_paid':True,'same_roi_evidence':regional,'art_approved':False},indent=2))
