import copy
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec=importlib.util.spec_from_file_location('reviewer_canary',Path(__file__).parents[1]/'reviewer_canary.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CanaryTests(unittest.TestCase):
 def metadata(self,path):
  return dict(id=m.ARTIFACT_ID,name='havenline-task10-critic-input-'+m.EVIDENCE_SHA,workflow_run=dict(id=m.RUN_ID,head_sha=m.EVIDENCE_SHA),expired=False,size_in_bytes=path.stat().st_size,digest='sha256:'+m.digest(path)),dict(id=m.RUN_ID,head_sha=m.EVIDENCE_SHA,status='completed',conclusion='failure')
 def test_metadata_bindings_and_diagnostic_failed_run(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'archive';p.write_bytes(b'fixture');artifact,run=self.metadata(p)
   with patch.object(m,'ARCHIVE_SIZE',p.stat().st_size),patch.object(m,'ARCHIVE_SHA',m.digest(p)):
    m.verify_archive(p,artifact,run)
    for key,value in [('id',0),('name','wrong'),('digest','sha256:'+'0'*64),('expired',True),('size_in_bytes',0),('workflow_run',dict(id=0,head_sha=m.EVIDENCE_SHA))]:
     bad=copy.deepcopy(artifact);bad[key]=value
     with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_archive(p,bad,run)
    for key,value in [('id',0),('head_sha','0'*40),('status','in_progress'),('conclusion','success')]:
     bad=dict(run);bad[key]=value
     with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_archive(p,artifact,bad)
 def test_safe_extract_rejects_hostile_paths_before_writing(self):
  for name in ['../escape','/escape','a/../../escape','a\\escape','C:/escape']:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as t:
    p=Path(t);archive=p/'a.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr(name,b'bad')
    with self.assertRaises(AssertionError):m.safe_extract(archive,p/'out')
    self.assertFalse((p/'out').exists())
 def test_safe_extract_rejects_symlink_and_duplicate(self):
  for mode in ['symlink','duplicate']:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as t:
    p=Path(t);archive=p/'a.zip'
    with zipfile.ZipFile(archive,'w') as z:
     if mode=='symlink':
      i=zipfile.ZipInfo('link');i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,'../escape')
     else:z.writestr('a/b','one');z.writestr('a/./b','two')
    with self.assertRaises(AssertionError):m.safe_extract(archive,p/'out')
 def envelope(self):
  review=dict(observations=['one','two'],defects=[])
  return dict(choices=[dict(finish_reason='stop',message=dict(content=json.dumps(review)))],usage=dict(completion_tokens=200))
 def test_actual_response_completion_and_contract_bounds(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);manifest=dict(critic_id='C3',groups=[dict(id='group')]);env=self.envelope();m.write(p/'group-raw.json',env)
   self.assertEqual(m.verify_responses(manifest,p)[0]['finish_reason'],'stop')
   for change in ['length','missing_usage','tokens','observations','defects']:
    bad=copy.deepcopy(env)
    if change=='length':bad['choices'][0]['finish_reason']='length'
    elif change=='missing_usage':bad.pop('usage')
    elif change=='tokens':bad['usage']['completion_tokens']=901
    else:
     review=json.loads(bad['choices'][0]['message']['content']);review[change]=['x'*161] if change=='observations' else ['defect']*6;bad['choices'][0]['message']['content']=json.dumps(review)
    m.write(p/'group-raw.json',bad)
    with self.subTest(change=change),self.assertRaises(AssertionError):m.verify_responses(manifest,p)
 def test_missing_group_and_c7_runner_token_limit(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);manifest=dict(critic_id='C7',groups=[dict(id='group')])
   with self.assertRaises(FileNotFoundError):m.verify_responses(manifest,p)
   env=self.envelope();env['usage']['completion_tokens']=901;m.write(p/'group-raw.json',env)
   with self.assertRaises(AssertionError):m.verify_responses(manifest,p)
   env=self.envelope();env['usage']['completion_tokens']=700;m.write(p/'group-raw.json',env)
   self.assertEqual(m.verify_responses(manifest,p)[0]['completion_tokens'],700)
   review=json.loads(env['choices'][0]['message']['content']);review['observations']=['x'*161,'two'];env['choices'][0]['message']['content']=json.dumps(review);m.write(p/'group-raw.json',env)
   with self.assertRaises(AssertionError):m.verify_responses(manifest,p)
 def test_workflow_is_dedicated_branch_fixed_evidence_and_matrix(self):
  text=(Path(__file__).parents[4]/'.github/workflows/havenline-task10-reviewer-canary.yml').read_text()
  for required in [m.BRANCH,str(m.RUN_ID),str(m.ARTIFACT_ID),m.EVIDENCE_SHA,'critic: [C3, C4, C7]','if: always()','ref: ${{ github.sha }}','workflow_dispatch:','  push:\n    branches: [havenline/T10-pipeline-canary]']:
   self.assertIn(required,text)
  self.assertNotIn('workflow_call:',text);self.assertNotIn('benchmark',text)
  self.assertIn('group: havenline-task10-reviewer-canary-${{ github.ref }}',text)
  self.assertIn('cancel-in-progress: false',text)

class ProvenanceTests(unittest.TestCase):
 def test_runtime_every_field_rejects_missing_null_substitution(self):
  execution=dict(local_independent_runtime=dict(provider='provider',base_model='model',model_revision='rev'))
  lock=dict(publisher='provider',base_model='model',revision='rev',runtime_release='release')
  record=dict(provider='provider',model='model',model_revision_actual='rev',model_revision_expected='rev',runtime_release='release')
  m.verify_runtime(record,execution,lock)
  for key in record:
   for mode in ('missing','null','substitute'):
    bad=dict(record)
    if mode=='missing':bad.pop(key)
    else:bad[key]=None if mode=='null' else 'wrong'
    with self.subTest(key=key,mode=mode),self.assertRaises(AssertionError):m.verify_runtime(bad,execution,lock)
 def request(self):
  return dict(max_tokens=900,temperature=0.2,top_p=0.9,seed=20260911,chat_template_kwargs=dict(enable_thinking=False),cache_prompt=False,response_format=dict(type='json_object',schema=dict(required=['scores'],properties=dict(scores=dict(type='object',properties=dict(dimension=dict(type='number',minimum=0,maximum=10)),required=['dimension'],additionalProperties=False),observations=dict(items=dict(type='string',maxLength=160),minItems=2,maxItems=2),defects=dict(items=dict(type='string',maxLength=160),maxItems=5)))))
 def test_request_controls_and_score_schema_reject_tampering(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);manifest=dict(groups=[dict(id='one'),dict(id='two')]);request=self.request()
   for name in ('one','two'):m.write(p/(name+'-request.json'),request)
   m.verify_requests(manifest,p,['dimension'])
   for key,value in [('max_tokens',901),('temperature',0.3),('top_p',0.8),('seed',0),('chat_template_kwargs',dict(enable_thinking=True)),('cache_prompt',True),('response_format',dict(type='text'))]:
    for mode in ('missing','substitute'):
     bad=copy.deepcopy(request)
     if mode=='missing':bad.pop(key)
     else:bad[key]=value
     m.write(p/'two-request.json',bad)
     with self.subTest(key=key,mode=mode),self.assertRaises(AssertionError):m.verify_requests(manifest,p,['dimension'])
   for change in ('lower','upper','dimension','required','extra_allowed','length','array'):
    bad=copy.deepcopy(request);props=bad['response_format']['schema']['properties'];scores=props['scores']
    if change=='lower':scores['properties']['dimension']['minimum']=-1
    elif change=='upper':scores['properties']['dimension']['maximum']=11
    elif change=='dimension':scores['properties']['extra']=dict(type='number',minimum=0,maximum=10)
    elif change=='required':scores['required']=[]
    elif change=='extra_allowed':scores['additionalProperties']=True
    elif change=='length':props['defects']['items']['maxLength']=161
    else:props['observations']['maxItems']=3
    m.write(p/'two-request.json',bad)
    with self.subTest(change=change),self.assertRaises(AssertionError):m.verify_requests(manifest,p,['dimension'])
   m.write(p/'two-request.json',request);m.write(p/'unexpected-request.json',request)
   with self.assertRaises(AssertionError):m.verify_requests(manifest,p,['dimension'])
