from pathlib import Path
from PIL import Image
import hashlib,io,json,subprocess,sys
P=Path(__file__).resolve().parent.parent
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
for d,h in {'receiver-site':'09b0f5b34361801c8a8c2d178d41be17ac9eb1b1993a4c95fff2944e11c10bf6','contoured-bearing':'5f2e2a1baf86048778a747dfafe582463b683e26f03b50be1234b4e9dd73c372','one-log-seat-spec':'f63ccc42003315401ca76ee2f89fd96c6d40a4244258725486e122c236ab710a'}.items():
 q=P/f'hvn-level1-rear-east-{d}-v1'
 assert sha(q/'SHA256SUMS')==h
 for line in (q/'SHA256SUMS').read_text().splitlines():
  digest,n=line.split();assert sha(q/n)==digest
site=P/'hvn-level1-rear-east-receiver-site-v1'
got=subprocess.check_output([sys.executable,site/'site.py',P/'hvn-pad-mount-admission/isolated-source/HavenlineLevel1',P/'hvn-counter-recovery/donor/north_counter_donor.tscn',P/'hvn-level1-three-carry-fit-v1/result.json'])
assert json.loads(got)==json.loads((site/'result.json').read_bytes())
source=P/'havenline-ref-audit/media/Media/Video-Misc/Screen_Recording_20260817_124510_YouTube.mp4'
assert sha(source)=='4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2'
selected={960:{'field':[(334,392),(373,404),(356,429)],'floor':[(295,420),(354,451)]},977:{'field':[(253,333),(283,354),(267,383),(227,361)],'floor':[(225,379),(272,402)]},995:{'field':[(221,302),(201,320)],'floor':[(257,362),(262,364)]},1010:{'field':[(151,300)],'floor':[(171,342)]}}
sample={}
for n,setpts in selected.items():
 d=subprocess.check_output(['ffmpeg','-v','error','-i',source,'-vf',f'select=eq(n\\,{n})','-frames:v','1','-f','image2pipe','-c:v','png','-'])
 im=Image.open(io.BytesIO(d)).convert('RGB');assert im.size==(1080,2520)
 im.thumbnail((432,1008))
 sample[n]={k:[{'xy':xy,'rgb':im.getpixel(xy)} for xy in xylist] for k,xylist in setpts.items()}
assert all(max(p['rgb'][0] for p in f['field'])<=88 and min(p['rgb'][0] for p in f['floor'])>=203 for f in sample.values())
print(json.dumps({'site_replayed_against_exact_input':True,'evidence_scope':'decoded sRGB reference contrast at explicit interior samples; never exact material','zero_based_frames_rgb_at_432x1008':sample},indent=2))
