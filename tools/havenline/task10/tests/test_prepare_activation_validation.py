"""Read-only validation state coverage; activation transitions remain narrower."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).parents[1]/'prepare_activation.py'
ROOT = SOURCE.parents[3]
FILES = ['T10/ACTIVATION_CHECKLIST.json','DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','CRITIC_MATRIX.json','task-gates.json','T10/FROZEN_SCOPE.md','T10/TASK_PACKET.md']
LEGAL = ['ASSIGNED','BUILDING_ISOLATED','BUILT_PENDING_DEPENDENCY','FIX_REQUIRED','BLOCKED','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW']

class ValidationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.docs=self.root/'Docs/Production'
  for rel in FILES:
   target=self.docs/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'Docs/Production'/rel,target)
  self.script=self.root/'tools/havenline/task10/prepare_activation.py';self.script.parent.mkdir(parents=True);shutil.copy2(SOURCE,self.script)
  spec=importlib.util.spec_from_file_location('t10_activation_validation_fixture',self.script);self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
 def mutate(self,rel,fn):
  p=self.docs/rel;data=json.loads(p.read_text());fn(data);p.write_text(json.dumps(data))
 def state(self,state):
  self.mutate('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T10'].update(status=state))
  self.mutate('WORKSTREAM_REGISTRY.json',lambda d:next(r for r in d['workstreams'] if r['task_id']=='T10').update(status=state))
  self.mutate('PATH_OWNERSHIP.json',lambda d:next(r for r in d['active_owners'] if r['task_id']=='T10').update(status=state))
  def gates(d):
   d.update(active_task='T10',active_status=state)
   for row in d.get('next_post_t03_wave',[]):
    if row['task']=='T10':row['state']=state
  self.mutate('task-gates.json',gates)
 def hashes(self):return {p.relative_to(self.docs).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.docs.rglob('*') if p.is_file()}
 def cli(self):
  before=self.hashes();p=subprocess.run([sys.executable,str(self.script)],cwd=self.root,capture_output=True,text=True);self.assertEqual(before,self.hashes());return p,json.loads(p.stdout)
 def test_all_legal_read_only_states_including_late_states(self):
  for state in LEGAL:
   with self.subTest(state=state):
    self.state(state);p,result=self.cli();self.assertEqual(p.returncode,0,result);self.assertFalse(result['integration_allowed']);self.assertFalse(result['task_approved'])
 def test_active_relock_or_preparation_rejects(self):
  for state in ('LOCKED','PREPARED'):
   self.state(state);p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('inactive unregistered topology' in e for e in result['errors']))
 def test_partial_state_and_approved_unknown_reject(self):
  for state in ['APPROVED','UNKNOWN']:
   self.state(state);p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertFalse(result['passed'])
  for rel,fn in [('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T10'].update(status='UNDER_REVIEW')),('WORKSTREAM_REGISTRY.json',lambda d:next(r for r in d['workstreams'] if r['task_id']=='T10').update(status='UNDER_REVIEW')),('PATH_OWNERSHIP.json',lambda d:next(r for r in d['active_owners'] if r['task_id']=='T10').update(status='UNDER_REVIEW')),('task-gates.json',lambda d:d.update(active_status='UNDER_REVIEW'))]:
   with self.subTest(authority=rel):
    self.state('FIX_REQUIRED');self.mutate(rel,fn);p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('disagreement' in e for e in result['errors']))
 def test_frozen_reservation_mismatch_rejects(self):
  self.state('FIX_REQUIRED');self.mutate('PATH_OWNERSHIP.json',lambda d:d['aliases']['@reservation:T10'].append('HavenlineGodot/scripts/unauthorized.gd'));p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('frozen planned reservation' in e for e in result['errors']))
 def test_future_task_unlocks_reject_across_authorities(self):
  cases=[('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T11'].update(status='PREPARED')),('WORKSTREAM_REGISTRY.json',lambda d:d['workstreams'].append(dict(task_id='T11',status='ASSIGNED'))),('PATH_OWNERSHIP.json',lambda d:d['active_owners'].append(dict(task_id='T11',status='ASSIGNED'))),('task-gates.json',lambda d:d['approved_tasks'].append('T11')),('task-gates.json',lambda d:d['completed_task_records'].update(T11={})),('task-gates.json',lambda d:d['next_post_t03_wave'].append(dict(task='T11',state='PREPARED')))]
  for rel,fn in cases:
   with self.subTest(authority=rel):
    original=(self.docs/rel).read_bytes();self.state('FIX_REQUIRED');self.mutate(rel,fn);p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('future task' in e for e in result['errors']));(self.docs/rel).write_bytes(original)
 def test_late_validation_cannot_activate_or_write_or_erase_history(self):
  for state in ['FIX_REQUIRED','BLOCKED','INTEGRATION_READY','INTEGRATING','UNDER_REVIEW']:
   with self.subTest(state=state):
    self.state(state);before=self.hashes()
    with patch.object(self.module,'git_head',return_value='a'*40):
     result=self.module.validate_activation('a'*40);self.assertFalse(result['passed'])
     with self.assertRaises(SystemExit):self.module.stage_activation('a'*40)
    self.assertEqual(before,self.hashes())
 def test_duplicate_or_missing_authorities_reject(self):
  self.state('FIX_REQUIRED')
  self.mutate('PATH_OWNERSHIP.json',lambda d:d['active_owners'].clear());p,result=self.cli();self.assertNotEqual(p.returncode,0)
  self.assertTrue(any('exactly one' in e for e in result['errors']))
 def test_real_historical_preactivation_topology_without_fake_registration(self):
  # Keep today's authorized isolated-build policy, but exercise the actual
  # four coordination files before any T10 registration/owner/active gates.
  historical='62f5a13753968c77a0feb47a18d93c82d8c5b581'
  for rel in ['DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','task-gates.json']:
   data=subprocess.check_output(['git','show',historical+':Docs/Production/'+rel],cwd=ROOT)
   (self.docs/rel).write_bytes(data)
  for state in ('LOCKED','PREPARED'):
   self.mutate('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T10'].update(status=state));p,result=self.cli();self.assertEqual(p.returncode,0,result);self.assertFalse(result['integration_allowed']);self.assertFalse(result['task_approved'])
  self.mutate('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T10'].update(status='ASSIGNED'));p,result=self.cli();self.assertNotEqual(p.returncode,0)
 def test_registered_bases_and_wave_must_match(self):
  self.state('FIX_REQUIRED')
  for rel,fn in [('WORKSTREAM_REGISTRY.json',lambda d:next(r for r in d['workstreams'] if r['task_id']=='T10').update(base_commit='b'*40)),('PATH_OWNERSHIP.json',lambda d:next(r for r in d['active_owners'] if r['task_id']=='T10').update(base_commit='b'*40)),('task-gates.json',lambda d:d.update(active_base_integration_commit='b'*40)),('task-gates.json',lambda d:next(r for r in d['next_post_t03_wave'] if r['task']=='T10').update(base_commit='b'*40)),('task-gates.json',lambda d:d.update(next_post_t03_wave=[r for r in d['next_post_t03_wave'] if r['task']!='T10'])),('task-gates.json',lambda d:d['next_post_t03_wave'].append(next(r.copy() for r in d['next_post_t03_wave'] if r['task']=='T10')))]:
   with self.subTest(authority=rel):
    original=(self.docs/rel).read_bytes();self.mutate(rel,fn);p,result=self.cli();self.assertNotEqual(p.returncode,0);(self.docs/rel).write_bytes(original)
  for key in ('activated_base_commit','activated_base_integration_commit','activation_base_commit'):
   original=(self.docs/'T10/ACTIVATION_CHECKLIST.json').read_bytes()
   self.mutate('T10/ACTIVATION_CHECKLIST.json',lambda d:d.update({key:'b'*40}));p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('activated base' in e for e in result['errors']));(self.docs/'T10/ACTIVATION_CHECKLIST.json').write_bytes(original)
  self.mutate('task-gates.json',lambda d:d.update(active_base_integration_commit='short'));p,result=self.cli();self.assertNotEqual(p.returncode,0)
 def test_inactive_topology_rejects_every_stale_active_pointer(self):
  historical='62f5a13753968c77a0feb47a18d93c82d8c5b581'
  for rel in ['DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','task-gates.json']:
   (self.docs/rel).write_bytes(subprocess.check_output(['git','show',historical+':Docs/Production/'+rel],cwd=ROOT))
  gate_path=self.docs/'task-gates.json';clean=json.loads(gate_path.read_text())
  for state in ('LOCKED','PREPARED'):
   self.mutate('DEPENDENCY_GRAPH.json',lambda d:d['tasks']['T10'].update(status=state))
   for field in [k for k in clean if k.startswith('active_')]+['active_unknown_future_pointer']:
    with self.subTest(state=state,field=field):
     dirty=dict(clean);dirty[field]='stale';gate_path.write_text(json.dumps(dirty));p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertTrue(any('inactive unregistered topology' in e for e in result['errors']))
   gate_path.write_text(json.dumps(clean))
 def test_registered_topology_matrix_rejects_partial_registration(self):
  for state in LEGAL:
   for missing in ('registry','owner','gate','wave'):
    with self.subTest(state=state,missing=missing):
     saved={rel:(self.docs/rel).read_bytes() for rel in ['DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json','task-gates.json']}
     self.state(state)
     if missing=='registry':self.mutate('WORKSTREAM_REGISTRY.json',lambda d:d.update(workstreams=[r for r in d['workstreams'] if r['task_id']!='T10']))
     elif missing=='owner':self.mutate('PATH_OWNERSHIP.json',lambda d:d.update(active_owners=[r for r in d['active_owners'] if r['task_id']!='T10']))
     elif missing=='gate':self.mutate('task-gates.json',lambda d:d.update({k:None for k in d if k.startswith('active_')}))
     else:self.mutate('task-gates.json',lambda d:d.update(next_post_t03_wave=[r for r in d['next_post_t03_wave'] if r['task']!='T10']))
     p,result=self.cli();self.assertNotEqual(p.returncode,0);self.assertFalse(result['passed'])
     for rel,data in saved.items():(self.docs/rel).write_bytes(data)
