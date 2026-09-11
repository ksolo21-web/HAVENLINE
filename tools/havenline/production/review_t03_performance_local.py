#!/usr/bin/env python3
"""Independent C6 early-budget critic for T03 using the checksum-pinned $0 local reviewer.
This is incremental subsystem review, not T68/T69 physical-device certification.
"""
from pathlib import Path
import hashlib,json,math,os,subprocess,time,urllib.request
ROOT=Path('task03-evidence');OUT=Path('task03-performance-review');OUT.mkdir(exist_ok=True)
CACHE=Path.home()/'.cache/havenline-t01-qwen35';SOURCE=os.environ['EXPECTED_SOURCE']
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
manifest=json.loads((CACHE/'manifest.json').read_text());assert manifest['base_model']=='Qwen/Qwen3.5-9B'
for item in manifest['files']:assert digest(CACHE/item['filename'])==item['sha256']
servers=list((CACHE/'runtime').rglob('llama-server'));assert len(servers)==1;server=servers[0]
prov=json.loads((ROOT/'provenance.json').read_text());tests=json.loads((ROOT/'tests.json').read_text());assert prov['source']==SOURCE and tests['source']==SOURCE and tests['all_passed']
gallery=json.loads((ROOT/'gallery/capture.json').read_text());native=json.loads((ROOT/'native4k/capture.json').read_text())
frames=gallery['captures']+native['captures'];draw=[int(x['draw_calls']) for x in frames];prims=[int(x['submitted_primitives']) for x in frames]
b=gallery['boundary']
metrics={
 'candidate':SOURCE,'functional_suites':tests['suite_count'],'functional_checks':tests['total_checks'],'t01_geometry_checks':tests['tree_geometry_checks'],
 'actual_capture_frames':len(frames),'native4k_scale1_frames':prov['native3840x2160_scale1_frames'],
 'scene_draw_calls_min':min(draw),'scene_draw_calls_max':max(draw),'scene_primitives_min':min(prims),'scene_primitives_max':max(prims),
 't03_incremental_draw_batches':b['draw_batches'],'collision_panels':b['collision_panel_instances'],'fence_visual_instances':b['fence_visual_instances'],'gate_post_instances':b['gate_post_instances'],'open_gate_leaf_instances':b['open_gate_leaf_instances'],
 'new_T03_GLBS':0,'new_T03_textures':0,'new_T03_animations':0,'new_T03_NPCs':0,'primitive_fence_meshes_created':b['primitive_fence_meshes_created'],
 'shared_panel_authority':b['visual_collision_share_panel_authority'],'render_scale':1.0,
 'final_physical_4k60_certified':False,'final_certification_tasks':['T68','T69']
}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2))
keys=['draw_call_batching','geometry_increment','shader_increment','physics_increment','animation_npc_increment','memory_storage_increment','thermal_risk_proxy']
schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5},'defects':{'type':'array','items':{'type':'string'},'maxItems':4},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':{k:{'type':'number','minimum':0,'maximum':10} for k in keys},'required':keys,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
prompt='''You are the independent Havenline C6 Performance Critic reviewing ONLY the incremental performance risk of Task T03 fences, gates and packed work lanes. This is an early subsystem budget gate, not final phone/tablet certification. T68/T69 separately require sustained physical native-4K/60 and thermals, so do not penalize T03 merely because those later hardware tests are not performed yet. Judge whether T03 consumes an unsustainable share of the future full-game budget from the supplied exact-source metrics. Important facts: T03 adds only two batched visual draw batches for its authored fence/post kit, uses existing GLBs/material infrastructure, creates no new texture/GLB/animation/NPC content, has 32 fence collision panels, and shares visual/collision panel authority. The actual engine capture metrics are whole-scene values, not T03-only values. Score draw_call_batching, geometry_increment, shader_increment, physics_increment, animation_npc_increment, memory_storage_increment, thermal_risk_proxy. Every score <=9.0 must cite an actionable T03-specific defect supported by the metrics. A >9 score means the incremental T03 load is comfortably bounded for this intermediate task. Return JSON only.'''
prompt+='\nExact metrics:\n'+json.dumps(metrics,sort_keys=True)
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','');log=(OUT/'inference.log').open('w')
cmd=[str(server),'-m',str(CACHE/manifest['model_file']),'--host','127.0.0.1','--port','8080','-c','8192','-t','4','-tb','4','-ngl','0','--parallel','1','--jinja']
proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
try:
 for _ in range(150):
  if proc.poll() is not None:raise RuntimeError('reviewer runtime exited')
  try:
   if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
  except Exception:pass
  time.sleep(2)
 else:raise RuntimeError('reviewer runtime not ready')
 body={'model':'T03-C6-performance','messages':[{'role':'user','content':prompt}],'max_tokens':800,'temperature':.2,'top_p':.9,'seed':20260911,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
 (OUT/'request.json').write_text(json.dumps(body,indent=2))
 req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req,timeout=900) as resp:raw=json.load(resp)
 (OUT/'raw.json').write_text(json.dumps(raw,indent=2));choice=raw['choices'][0];assert choice['finish_reason']=='stop';review=json.loads(choice['message']['content']);(OUT/'review.json').write_text(json.dumps(review,indent=2))
 scores=review['scores'];assert set(scores)==set(keys) and all(type(v) in (int,float) and not isinstance(v,bool) and math.isfinite(v) for v in scores.values())
 passed=min(scores.values())>9.0 and review['defects']==[] and review['coverage_complete'] is True and review['confidence'] in ('medium','high')
 result={'task':'T03','critic_id':'C6','candidate_commit':SOURCE,'independent':True,'provider':'local-checksum-pinned-public-model','model':manifest['base_model'],'model_revision':manifest['revision'],'run_id':os.environ.get('GITHUB_RUN_ID','local'),'mandatory_dimensions':scores,'minimum':min(scores.values()),'defects':review['defects'],'coverage_complete':review['coverage_complete'],'confidence':review['confidence'],'passed':passed,'physical_device_certification':False,'raw_output_path':'task03-performance-review/raw.json','raw_output_sha256':digest(OUT/'raw.json')}
 (OUT/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(0 if passed else 1)
finally:
 proc.terminate()
 try:proc.wait(timeout=15)
 except:proc.kill()
 log.close()
