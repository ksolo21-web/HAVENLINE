import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).parents[1]))
import export_closure_records as m

class ExportTests(unittest.TestCase):
 def fixture(self,root):
  archive=root/'artifact.zip'
  payload={'candidate':'a'*40,'files':{'proof.json':hashlib.sha256(b'{}').hexdigest()}}
  with zipfile.ZipFile(archive,'w') as z:
   z.writestr('proof.json',b'{}');z.writestr('evidence-index.json',json.dumps(payload))
  run=dict(id=123,head_sha='a'*40,status='completed',conclusion='success')
  artifact=dict(id=456,name='havenline-task10-critic-input-'+'a'*40,workflow_run=dict(id=123,head_sha='a'*40),expired=False,size_in_bytes=archive.stat().st_size,digest='sha256:'+m.sha(archive),created_at='2026-09-18T00:00:00Z',expires_at='2026-12-17T00:00:00Z')
  return archive,artifact,run
 def test_archive_identity_and_index(self):
  with tempfile.TemporaryDirectory() as t:
   archive,artifact,run=self.fixture(Path(t))
   data=m.verify_archive(archive,artifact,run,'a'*40,True)
   self.assertEqual(1,len(m.verify_index(data,'a'*40)['files']))
   for key,value in [('status','in_progress'),('conclusion','failure'),('head_sha','b'*40)]:
    with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_archive(archive,artifact,dict(run,**{key:value}),'a'*40,True)
   for key,value in [('digest','sha256:'+'0'*64),('expired',True),('size_in_bytes',0),('expires_at','2026-10-18T00:00:00Z'),('workflow_run',dict(id=999,head_sha='a'*40))]:
    with self.subTest(key=key),self.assertRaises(AssertionError):m.verify_archive(archive,dict(artifact,**{key:value}),run,'a'*40,True)
   data['proof.json']=b'{"tamper":true}'
   with self.assertRaises(AssertionError):m.verify_index(data,'a'*40)
 def test_unknown_or_missing_payload_rejects(self):
  with tempfile.TemporaryDirectory() as t:
   a,b,c=self.fixture(Path(t));data=m.verify_archive(a,b,c,'a'*40)
   for mutated in [dict(data,unknown=b'x'),{k:v for k,v in data.items() if k!='proof.json'}]:
    with self.assertRaises(AssertionError):m.verify_index(mutated,'a'*40)
 def test_canonical_keeps_original_scores_and_confidence(self):
  record=dict(scores={'frame_time':9.375},confidence='medium',coverage_complete=True,defects=[],input_manifest_hash='b'*64,provider='actual reviewer',model='actual model',request_or_run_id='actual request')
  raw=(b'original record',b'original raw',record)
  out=m.canonical('C6',raw,'a'*40,dict(id=1),dict(id=2,digest='sha256:'+'c'*64),'d'*64,'e'*40)
  self.assertEqual(record['scores'],out['scores']);self.assertEqual('medium',out['confidence']);self.assertFalse(out['score_reuse'])
  for change in [dict(scores={'frame_time':9}),dict(defects=['defect']),dict(confidence='low'),dict(coverage_complete=False)]:
   with self.assertRaises(AssertionError):m.canonical('C6',(raw[0],raw[1],dict(record,**change)),'a'*40,dict(id=1),dict(id=2,digest='sha256:'+'c'*64),'d'*64,'e'*40)
 def test_bundle_is_deterministic_and_preserves_bytes(self):
  import io
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'raw.txt').write_bytes(b'original\x00bytes')
   one=m.original_bundle(root);self.assertEqual(one,m.original_bundle(root))
   with zipfile.ZipFile(io.BytesIO(one)) as z:self.assertEqual(b'original\x00bytes',z.read('raw.txt'))
 def test_missing_duplicate_and_stale_critic_identity_rejects(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   with self.assertRaises(AssertionError):m.verify_reviews(root,{},'a'*40)
   for cid in m.CRITICS:(root/cid).mkdir()
   (root/'C1'/'critic-record.json').write_text(json.dumps(dict(raw_output_path='raw.json',raw_output_hash='0'*64)))
   (root/'C1'/'raw.json').write_text('{}')
   with self.assertRaises(AssertionError):m.verify_reviews(root,{},'a'*40)

class FullReviewExportTests(unittest.TestCase):
 def prepare(self,root):
  execution=m.load(m.ROOT/'Docs/Production/CRITIC_EXECUTION.json')
  matrix=m.load(m.ROOT/'Docs/Production/CRITIC_MATRIX.json')
  from critic_profile import resolve_critic
  candidate='a'*40;payload={}
  perf=dict(candidate_commit=candidate,**{k:0 for k in ['visible_triangles','draw_calls','materials_visible','texture_gpu_memory_mb','process_memory_mb','physics_active_bodies','animated_rigs_active','npc_companion_active_population','storage_download_mb']})
  payload['performance.json']=m.encoded(perf)
  for cid in m.CRITICS:
   folder=root/cid;folder.mkdir()
   spec,_=resolve_critic('T10',cid,execution,matrix)
   raw=dict(scores={d:9.5 for d in spec['dimensions']},defects=[],coverage_complete=True,confidence='high')
   manifest=dict(candidate_commit=candidate,critic_id=cid,groups=[dict(id='fixture',items=[])])
   record=dict(raw,task_id='T10',critic_id=cid,candidate_hash=candidate,independent_runtime=True,provider='synthetic-test-provider',model='synthetic-test-model',request_or_run_id='synthetic-test-request',raw_output_path='raw-output.json')
   if cid in ('C3','C4','C7'):
    runtime=execution['local_independent_runtime'];record.update(provider=runtime['provider'],model=runtime['base_model'],model_revision_actual=runtime['model_revision'],model_revision_expected=runtime['model_revision'],request_or_run_id='123/synthetic-test-job')
    raw=dict(candidate=candidate,critic_id=cid,fatal_error=None,groups=[dict(group='fixture',passed=True,review=raw)])
   if cid=='C6':
    raw.update(candidate_hash=candidate,critic_id=cid)
    manifest['groups'][0]['items']=[dict(path='critic-input/performance.json',kind='json',category='quantitative_budgets',sha256=hashlib.sha256(payload['performance.json']).hexdigest())]
   payload[cid+'-manifest.json']=m.encoded(manifest)
   record['input_manifest_hash']=hashlib.sha256(payload[cid+'-manifest.json']).hexdigest()
   (folder/'raw-output.json').write_bytes(m.encoded(raw));record['raw_output_hash']=m.sha(folder/'raw-output.json')
   (folder/'critic-record.json').write_bytes(m.encoded(record))
  return payload,candidate
 def test_complete_originals_validate_without_score_assignment(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);payload,candidate=self.prepare(root)
   result=m.verify_reviews(root,payload,candidate,123)
   self.assertEqual(set(m.CRITICS),set(result))
   for cid,value in result.items():self.assertEqual((root/cid/'critic-record.json').read_bytes(),value[0])
 def test_record_provenance_score_and_source_tampering_reject(self):
  for cid,key,value in [('C3','provider','forged'),('C3','model','forged'),('C3','request_or_run_id','999/other'),('C3','model_revision_actual','0'*40),('C1','candidate_hash','b'*40),('C1','confidence','medium'),('C1','scores',{'reference_fidelity':10}),('C6','input_manifest_hash','0'*64)]:
   with self.subTest(cid=cid,key=key),tempfile.TemporaryDirectory() as t:
    root=Path(t);payload,candidate=self.prepare(root);path=root/cid/'critic-record.json';record=m.load(path);record[key]=value;path.write_bytes(m.encoded(record))
    with self.assertRaises(AssertionError):m.verify_reviews(root,payload,candidate,123)

class ClosureBindingTests(ExportTests):
 def test_ninety_day_retention_rejects_other_settings(self):
  with tempfile.TemporaryDirectory() as t:
   archive,artifact,run=self.fixture(Path(t))
   for expiry in ('2026-12-16T00:00:00Z','2026-12-18T00:00:00Z'):
    with self.assertRaises(AssertionError):m.verify_archive(archive,dict(artifact,expires_at=expiry),run,'a'*40,True)
 def test_all_manifest_bytes_are_indexed_and_canonical_index_is_bound(self):
  with tempfile.TemporaryDirectory() as t:
   a,b,c=self.fixture(Path(t));payload=m.verify_archive(a,b,c,'a'*40)
   row=json.loads(m.canonical_index(payload,'a'*40))
   self.assertEqual(('T10','a'*40,1),(row['task_id'],row['candidate_commit'],row['file_count']))
   self.assertEqual(hashlib.sha256(payload['evidence-index.json']).hexdigest(),row['source_evidence_index_sha256'])
   payload['C3-manifest.json']=b'{}'
   with self.assertRaises(AssertionError):m.verify_index(payload,'a'*40)
 def test_manifest_and_original_archive_survive_bundle(self):
  import io
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'raw.txt').write_text('original')
   bundle=m.original_bundle(root,b'exact manifest',b'exact downloaded zip')
   with zipfile.ZipFile(io.BytesIO(bundle)) as z:
    self.assertEqual(b'exact manifest',z.read('input-manifest.json'))
    self.assertEqual(b'exact downloaded zip',z.read('actions-artifact.zip'))
   (root/'input-manifest.json').write_text('collision')
   with self.assertRaises(AssertionError):m.original_bundle(root,b'new')
 def test_hosted_artifacts_bind_consumed_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);records=root/'records';records.mkdir();metadata={};run=dict(id=123,head_sha='a'*40,status='completed',conclusion='success')
   for cid in ('C3','C4','C7'):
    directory=records/cid;directory.mkdir();(directory/'critic-record.json').write_bytes(b'original')
    archive=root/(cid+'.zip')
    with zipfile.ZipFile(archive,'w') as z:z.writestr('specialist-review/critic-record.json',b'original')
    metadata[cid]=dict(archive=str(archive),artifact=dict(id=len(metadata)+1,name=f'havenline-task10-{cid}-'+('a'*40),workflow_run=dict(id=123,head_sha='a'*40),expired=False,size_in_bytes=archive.stat().st_size,digest='sha256:'+m.sha(archive)))
   self.assertEqual(3,len(m.verify_hosted_artifacts(metadata,records,run,'a'*40)))
   for key,value in [('name','wrong'),('digest','sha256:'+'0'*64),('workflow_run',dict(id=124,head_sha='a'*40))]:
    bad=copy.deepcopy(metadata);bad['C3']['artifact'][key]=value
    with self.assertRaises(AssertionError):m.verify_hosted_artifacts(bad,records,run,'a'*40)
   (records/'C3'/'critic-record.json').write_bytes(b'tampered')
   with self.assertRaises(AssertionError):m.verify_hosted_artifacts(metadata,records,run,'a'*40)
 def test_export_commit_must_descend_from_integration_head(self):
  import subprocess
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   def git(*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.DEVNULL).decode().strip()
   git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
   git('commit','--allow-empty','-m','candidate');candidate=git('rev-parse','HEAD')
   git('commit','--allow-empty','-m','integration');integration=git('rev-parse','HEAD')
   git('commit','--allow-empty','-m','export');export=git('rev-parse','HEAD')
   git('checkout','--orphan','unrelated');git('commit','--allow-empty','-m','unrelated');unrelated=git('rev-parse','HEAD')
   with patch.object(m,'ROOT',root):
    m.verify_export_lineage(candidate,integration,export)
    with self.assertRaises(subprocess.CalledProcessError):m.verify_export_lineage(candidate,integration,unrelated)
