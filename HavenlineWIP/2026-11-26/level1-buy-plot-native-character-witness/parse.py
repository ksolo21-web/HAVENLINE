"""Read-only independent parser. Never opens Godot or authorizes an action."""
import hashlib,json,math,re,sys
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parent
REF=root.parent/'hvn-l1-grounded-construction-marker-icon-v2-native-v1/graphics-evidence.UCJRgmak'
assert hashlib.sha256((REF/'v2-evidence.json').read_bytes()).hexdigest()=='9f12f603bbf2960ad1763b7bdaadb4abf048704d4119e6e627dcf9ad65c289ef'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
names=['funded-approach-moving','funded-near-moving','first-committed']
png=['9628c8a4f02575cb8fcbbf290859386c95f11e9b9a50a91b5a2c499ac68eb2a8','599a0dd87f8e8c103c5bbfb83999a5f4f6357af3a7fe49cb41966c23f3999544','3be92e19d3b2876e5b4fad91132e7b497459241803bb2541f785be838576d805']
def read(f,key):
 return [json.loads(x.split(' ',1)[1]) for x in f.read_text().splitlines() if x.startswith(key+' ')]
def tf(row):
 assert len(row)==4 and all(len(v)==3 and all(math.isfinite(x) for x in v) for v in row)
 a,b,c,_=row
 det=a[0]*(b[1]*c[2]-b[2]*c[1])-b[0]*(a[1]*c[2]-a[2]*c[1])+c[0]*(a[1]*b[2]-a[2]*b[1])
 assert abs(det)>1e-10
 return det
def close(a,b):
 return len(a)==len(b) and max(abs(x-y) for x,y in zip(a,b))<5e-5
ref=read(REF/'enabled.log','L1_PAD_DRAW')
assert len(ref)==3
for a,n,b in zip(ref,names,png):
 assert a['phase']==n and sha(REF/'enabled'/f'{n}.png')==b
if sys.argv[1:]==['--pins-only']:
 print(json.dumps({'input_record_pinned':True,'has_live_pose_witness':False}));sys.exit(0)
assert len(sys.argv)==2
out=Path(sys.argv[1]); log=out/'enabled.log'; raw=log.read_text()
assert not re.search(r'REJECT|^FAIL |SCRIPT ERROR|Parse Error',raw,re.M)
assert read(log,'L1_PAD_FINAL')==[{'candidate':True,'checks':23,'failures':0,'ticks':[10,310,354,357],'drawn':names}]
actual=read(log,'L1_PAD_DRAW')
assert actual==ref
assert (out/'no-persistence.txt').read_text()=='stock ephemeral: no save flag or isolated receipt files\n'
p=out/'enabled'
assert sorted(x.name for x in p.glob('*.pose.json'))==sorted(x+'.pose.json' for x in names[:2])
summary=[]; matrices={}
for i,(js,n,old) in enumerate(zip(actual,names,png)):
 f=p/(n+'.png'); im=Image.open(f)
 assert im.mode=='RGBA' and im.size==(1280,720) and sha(f)==old and hashlib.sha256(im.tobytes()).hexdigest()==js['pixel_sha256']
 if i==2:continue
 report=p/(n+'.pose.json'); o=json.loads(report.read_text()); j=js['draw']
 assert o['tick']==j['tick']==[346,355][i] and o['physics']==j['physics_frame']
 assert o['size']==13.0 and o['projection']==1 and o['viewport']==[1280,720] and close(o['offset'],[0,0])
 assert close(o['camera'][3],j['camera']) and close(o['actor'][3],j['actor']) and j['grounded']
 assert j['wood']==j['ledger_cost']==3 and j['sources']==['wood-b','wood-c','wood-a'] and not j['receipt'] and j['distance_xz']>.72
 assert o['phase'] and math.isfinite(o['phase_seconds']) and o['phase_seconds']>=0
 for q in (o['camera'],o['actor']): tf(q)
 surfaces=o['surfaces']; assert len({q['relative'] for q in surfaces})==len(surfaces)>0
 sk=[q for q in surfaces if q['palette']]; assert len(sk)==1
 sk=sk[0]; tf(sk['skeleton_world']); binds=sk['palette']
 assert len(binds)==66 and {q['bind'] for q in binds}=={q['bone'] for q in binds}==set(range(66))
 for q in binds:
  tf(q['pose']); tf(q['inverse'])
 for q in surfaces:
  tf(q['world'])
  assert q['surfaces'] and all(a['vertices']>0 and (a['indices'] or a['vertices'])%3==0 for a in q['surfaces'])
  for a in q['surfaces']:
   assert a['weights'] in ([4*a['vertices'],8*a['vertices']] if q is sk else [0])
 summary.append({'tick':j['tick'],'pose_sha256':sha(report),'scene_meshes':len(surfaces),'clip':o['phase'],'phase_seconds':o['phase_seconds']})
 matrices[i]=hashlib.sha256(json.dumps([q['pose'] for q in binds],separators=(',',':')).encode()).hexdigest()
assert matrices[0]!=matrices[1], 'must capture distinct native dynamic palettes'
print(json.dumps({'matched_exact_prior_pixels_and_state':True,'paid_frame_byte_exact':True,'checks':23,'witnesses':summary,
                  'not_a_stencil_or_parser_scope_beyond_two_poses':True},indent=2))
