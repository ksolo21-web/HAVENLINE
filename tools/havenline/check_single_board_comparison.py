#!/usr/bin/env python3
"""Blind comparison controls, never a candidate quality verdict.

The preceding two-image control hallucinated differences between identical PNGs.
This changes only how images are presented: one clearly labelled board per call.
The model must distinguish both unchanged reference pairs and a changed pair.
"""
from pathlib import Path
import base64,hashlib,io,json,os,subprocess,time,urllib.request
from PIL import Image,ImageDraw
ROOT=Path('Docs/Production/T01/ActualReview/R9');OUT=Path('comparison-control');OUT.mkdir(exist_ok=True)
CACHE=Path.home()/'.cache/havenline-t01-gemma'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4194304),b''):h.update(block)
 return h.hexdigest()
m=json.loads((CACHE/'manifest.json').read_text())
assert m['base_model']=='google/gemma-3-12b-it' and m['revision']=='05c2df468ad7a0bb1284b3d6fe2bdf495a885567'
for item in m['files']:assert sha(CACHE/item['filename'])==item['sha256']
reference=Image.open(ROOT/'reference-detail.webp').convert('RGB')
assert sha(ROOT/'reference-detail.webp')=='25b0e78c93f13ddadb8b815e7e19daf68485471d2be3fed0dd99bde8d00c48af'
# One reference tree, not a pair of visually different reference trees per panel.
ref=reference.crop((0,0,220,300))
human=Image.open(ROOT/'clearance/clearance-baseline.png').convert('RGB').crop((1470,705,2370,1665))
controls=[('control-A',ref,ref,True),('control-B',ref,human,False)]
request_prompt='Two panels are labelled LEFT and RIGHT in this one image. Compare their pictured content, ignoring labels and borders. Is the pictured content identical? Briefly identify what is visible in LEFT and RIGHT and describe any real differences. Do not assume that two similar scenes are identical, and do not invent differences. Return JSON only.'
schema={'type':'object','properties':{'same_content':{'type':'boolean'},'left_subject':{'type':'string'},'right_subject':{'type':'string'},'visible_differences':{'type':'string'},'confidence':{'type':'string','enum':['low','medium','high']}},'required':['same_content','left_subject','right_subject','visible_differences','confidence'],'additionalProperties':False}
server=next((CACHE/'runtime').rglob('llama-server'));env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
log=(OUT/'inference.log').open('w');proc=subprocess.Popen([str(server),'-m',str(CACHE/m['model_file']),'--mmproj',str(CACHE/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja'],env=env,stdout=log,stderr=subprocess.STDOUT)
records=[];error=None
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('Reviewer exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('Reviewer startup failed')
 for name,left,right,expected in controls:
  board=Image.new('RGB',(720,500),(235,238,241));d=ImageDraw.Draw(board)
  for i,(label,image) in enumerate([('LEFT',left),('RIGHT',right)]):
   image=image.copy();image.thumbnail((340,460),Image.Resampling.LANCZOS)
   board.paste(image,(i*360+(360-image.width)//2,34));d.text((i*360+10,10),label,fill='black')
  path=OUT/(name+'.png');board.save(path);b=io.BytesIO();board.save(b,format='PNG')
  req={'model':'blind-comparison-control','messages':[{'role':'user','content':[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()}},{'type':'text','text':request_prompt}]}],'max_tokens':190,'temperature':.1,'seed':20260908,'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
  with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(req).encode(),headers={'Content-Type':'application/json'}),timeout=600) as r:raw=json.load(r)
  (OUT/(name+'-raw.json')).write_text(json.dumps(raw,indent=2));choice=raw['choices'][0]
  assert choice['finish_reason']=='stop';value=json.loads(choice['message']['content'])
  record={'name':name,'input_sha256':sha(path),'expected_identical_not_supplied_to_model':expected,'response':value,'passed':value['same_content'] is expected and value['confidence']!='low'}
  records.append(record);print(json.dumps(record),flush=True)
except Exception as exc:error=str(exc)
finally:
 (OUT/'controls.json').write_text(json.dumps({'model':m['base_model'],'revision':m['revision'],'records':records,'error':error,'comparison_controls_passed':len(records)==2 and all(r['passed'] for r in records),'not_game_approval':True,'task_approved':False,'game_images_unmodified':True},indent=2))
 (OUT/'prompt.txt').write_text(request_prompt)
 proc.terminate()
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:proc.kill()
 log.close()
