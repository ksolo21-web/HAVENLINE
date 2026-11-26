import sys,json,hashlib,re,math
from pathlib import Path
from PIL import Image
r=Path(sys.argv[1])
expected={
 'write':[('fresh-spawn',0,0,False,False,False),('paid-first-frame',0,0,True,False,False),
 ('south-bidirectional',0,0,True,True,False),('east-bidirectional',0,0,True,True,True),
 ('writer-v2',1,1,True,True,True)],
 'cold':[('cold-v2-no-replay',1,1,True,False,False)]}
h=lambda b:hashlib.sha256(b).hexdigest()
out={}
for phase, items in expected.items():
 text=(r/(phase+'.log')).read_text()
 assert re.search(r'^Godot Engine v4\.7\.2\.stable\.official\.ed1daf0bf ',text,re.M)
 assert re.search(r'^OpenGL .* - Compatibility - Using Device: Mesa - llvmpipe ',text,re.M)
 messages=re.findall(r'^.*(?:ERROR:|WARNING:|^FAIL |DRAW_REJECT|Parse Error).*$',text,re.M)
 assert messages in ([], ['WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.'])
 assert f"L1_STOCK_POST_DRAW_OK {phase} {len(items)}" in text.splitlines()
 count={'write':57,'cold':10}[phase]
 assert f"L1_COMBINED_ROUTE phase={phase} checks={count} failures=0" in text.splitlines()
 assert len(re.findall("^PASS ",text,re.M))==count
 draw=[json.loads(row) for row in re.findall(r'^L1_POST_DRAW (.+)$',text,re.M)]
 assert [v['phase'] for v in draw]==[x[0] for x in items]
 for v,(tag,s,k,p,sg,eg) in zip(draw,items):
  assert v['viewport_px']==v['image_px']==[1280,720] and v['display']=='X11' and v['camera_ortho']==13
  assert v['draw']['physics_frames']-v['queued']['physics_frames'] in (0,1)
  for snap in (v['queued'],v['draw']):
   assert tuple(snap[t] for t in ['stock','renewals','paid','south_open','east_open'])==(s,k,p,sg,eg)
   assert snap['camp_visible'] is p and snap['pad_hidden'] is p and snap['hearth_center_paid']
  name=r/(tag+'.png')
  with Image.open(name) as im:
   assert im.size==(1280,720) and im.format=='PNG'
   pix=im.convert('RGB'); n=len(pix.getcolors(maxcolors=921600))
   assert n>=64 and v['pixel_sha256'] in {h(pix.tobytes()),h(im.convert('RGBA').tobytes())}
  out[tag]={'png_sha256':h(name.read_bytes()),'native_sha256':v['pixel_sha256'],'rgb_color_count':n,
   'queued_tick':v['queued']['tick'],'actor_displacement_within_draw_m':math.dist(v['queued']['actor'],v['draw']['actor'])}
assert set(out)=={p.stem for p in r.glob('*.png')}
assert len({q['native_sha256'] for q in out.values()})==6
print(json.dumps(out,indent=2))
