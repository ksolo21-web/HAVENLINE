import copy,json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import source_packets as m
import source_packet_aggregate as a

SOURCE=(Path(__file__).resolve().parents[4]/m.SOURCE_PATH).read_text()
C='a'*40;T='b'*40
class AggregateTests(unittest.TestCase):
 def fixture(self,root):
  plan=m.packets(SOURCE,C,T)
  for group,packet in plan['groups'].items():
   out=root/group;out.mkdir()
   manifest=json.dumps(plan,ensure_ascii=False,indent=2).encode();(out/'packet-manifest.json').write_bytes(manifest)
   review=dict(observations=['Inspected fixture.','Synthetic unit test only.'],defects=[],coverage_complete=True,confidence='high',scores={d:9.5 for d in m.DIMENSIONS})
   raw=json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(review)}}]}).encode();(out/'review.response.json').write_bytes(raw)
   row=dict(source=C,tree=T,source_sha256=plan['source']['sha256'],group=group,functions=packet['functions'],prompt_sha256=packet['prompt_sha256'],passed=True,task_approved=False,non_voting=True,final_critic_vote=False,token_admission_passed=True,provider='unsloth/Qwen3.5-9B-GGUF',model='Qwen/Qwen3.5-9B',revision='3885219b6810b007914f3a7950a8d1b469d598a5',runtime_release='b10809',input_tokens=1000,input_manifest_sha256=m.digest(manifest),raw_response_sha256=m.digest(raw),review=review,errors=[])
   (out/'group-result.json').write_text(json.dumps(row))
 def test_complete_fixture_passes(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);r=a.aggregate(root,C,T,SOURCE)
   self.assertTrue(r['passed'],r);self.assertEqual(37,r['covered_primary_functions']);self.assertFalse(r['task_approved'])
 def test_no_packets_fails(self):
  with tempfile.TemporaryDirectory() as temp:self.assertFalse(a.aggregate(Path(temp),C,T,SOURCE)['passed'])
 def test_each_binding_and_fail_state_blocks(self):
  for field,value in [('source','c'*40),('tree','c'*40),('passed',False),('passed',1),('tool_error','timeout'),('input_tokens',4097),('raw_response_sha256','0'*64),('input_manifest_sha256','0'*64),('functions',[]),('revision','0'*40)]:
   with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);self.fixture(root);p=root/'lighting/group-result.json';r=json.loads(p.read_text());r[field]=value;p.write_text(json.dumps(r));self.assertFalse(a.aggregate(root,C,T,SOURCE)['passed'])
 def test_missing_and_duplicate_packet_rejected(self):
  import shutil
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);shutil.copytree(root/'lighting',root/'duplicate');self.assertFalse(a.aggregate(root,C,T,SOURCE)['passed'])
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);(root/'lighting/group-result.json').unlink();self.assertFalse(a.aggregate(root,C,T,SOURCE)['passed'])
 def test_raw_response_change_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);(root/'lighting/review.response.json').write_text('{}');self.assertFalse(a.aggregate(root,C,T,SOURCE)['passed'])

if __name__=='__main__':unittest.main()
