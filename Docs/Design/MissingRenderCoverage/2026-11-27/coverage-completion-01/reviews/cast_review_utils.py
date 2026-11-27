from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent.parent
def bind(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def new_review(n,scope='STATIC BODY REFERENCE ONLY'):
 i=ROOT/'invocations'/f'{n}.json';v=json.loads(i.read_text());p=ROOT/'reviews/evidence'/f'{n}-crop-provenance.json';d=json.loads(p.read_text())
 assert bind(v['output']['local_path'])['sha256']==v['output']['sha256']==d['source_sha256']
 return {'schema_version':1,'review_id':n+'-independent','reviewer':'/root/missing_cast_critic','independent':True,'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'PENDING REVIEW','scope':scope,'score_method':'Minimum mandatory visual-area score, not an average; every mandatory static visual check must pass strictly above 9.0.','reviewed_image':v['output'],'requirements_at_generation':v['requirements_at_generation'],'requirements_snapshot':bind(v['requirements_snapshot_path']),'invocation':bind(i),'exact_actual_prompt':bind(v['exact_actual_prompt_file']['local_path']),'source_images_inspected':v['ordered_reference_inputs'],'actual_full_native_png_inspected':True,'crop_provenance':bind(p),'actual_native_crops_inspected':[x['id'] for x in d['crops']],'native_mesh_rig_animation_runtime_approval':False,'pending_separate_evidence':['Full GitHub byte/blob readback and independent archive gate'],'preservation':'All previous source identities, original accepted images, rejected iterations and exact prompts remain preserved.'}
def area(i,s,f,status='PASS',evidence=None):
 d={'id':i,'score':s,'status':status,'finding':f}
 if evidence:d['evidence']=evidence
 return d
def save_review(n,r):
 r['score']=min(x['score'] for x in r['areas']);r['all_mandatory_visual_checks_passed']=all(x['score']>9 and x['status']=='PASS' for x in r['areas']) and not r.get('mandatory_defects_remaining',[])
 r['status']=('PASS — ' if r['all_mandatory_visual_checks_passed'] else 'REPAIR REQUIRED — ')+r['scope']
 p=ROOT/'reviews'/f'critic-{n}.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(p),'status':r['status'],'score':r['score'],'review_sha256':bind(p)['sha256'],'image_sha256':r['reviewed_image']['sha256']}))
