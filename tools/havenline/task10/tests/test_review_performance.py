import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import review_performance as m

class PerformanceReviewTests(unittest.TestCase):
    def fixture(self,root,change=None):
        candidate='a'*40
        manifest=dict(task_id='T10',critic_id='C6',candidate_commit=candidate,groups=[dict(id='measured-performance')])
        mp=root/'manifest.json';mp.write_text(json.dumps(manifest))
        dims=['frame_time','draw_calls','geometry','texture_memory','shader_cost','physics','animation','population','thermal_risk']
        raw=dict(candidate_hash=candidate,critic_id='C6',scores={d:9.5 for d in dims},defects=[],coverage_complete=True,confidence='high')
        if change:change(raw)
        rp=root/'raw.json';rp.write_text(json.dumps(raw))
        record=dict(raw,task_id='T10',provider='test fixture',model='test fixture',request_or_run_id='synthetic-only',independent_runtime=True,input_manifest_hash=hashlib.sha256(mp.read_bytes()).hexdigest(),raw_output_path=str(rp),raw_output_hash=hashlib.sha256(rp.read_bytes()).hexdigest())
        recordp=root/'record.json';recordp.write_text(json.dumps(record))
        perf=dict(candidate_commit=candidate,**{k:1 for k in ['visible_triangles','draw_calls','materials_visible','texture_gpu_memory_mb','process_memory_mb','physics_active_bodies','animated_rigs_active','npc_companion_active_population','storage_download_mb']})
        pp=root/'perf.json';pp.write_text(json.dumps(perf))
        manifest['groups'][0]['items']=[dict(path='critic-input/performance.json',kind='json',category='quantitative_budgets',sha256=hashlib.sha256(pp.read_bytes()).hexdigest())]
        mp.write_text(json.dumps(manifest));record['input_manifest_hash']=hashlib.sha256(mp.read_bytes()).hexdigest();recordp.write_text(json.dumps(record))
        return recordp,mp,pp,candidate
    def test_scored_and_quantitative_both_pass(self):
        with tempfile.TemporaryDirectory() as t:self.assertTrue(m.validate(*self.fixture(Path(t)))['passed'])
    def test_missing_low_scores_defect_and_incomplete_reject(self):
        changes=[lambda r:r['scores'].pop('thermal_risk'),lambda r:r['scores'].update(frame_time=9.0),lambda r:r.update(defects=['defect']),lambda r:r.update(coverage_complete=False)]
        for change in changes:
            with tempfile.TemporaryDirectory() as t:self.assertFalse(m.validate(*self.fixture(Path(t),change))['passed'])
    def test_stale_hash_or_provenance_reject(self):
        for field,value in [('candidate_hash','b'*40),('input_manifest_hash','0'*64),('raw_output_hash','0'*64),('independent_runtime',False),('provider','')]:
            with tempfile.TemporaryDirectory() as t:
                args=self.fixture(Path(t));record=json.loads(args[0].read_text());record[field]=value;args[0].write_text(json.dumps(record))
                with self.subTest(field=field),self.assertRaises(AssertionError):m.validate(*args)
    def test_quantitative_failure_cannot_be_hidden(self):
        with tempfile.TemporaryDirectory() as t:
            args=self.fixture(Path(t));perf=json.loads(args[2].read_text());perf['candidate_commit']='b'*40;args[2].write_text(json.dumps(perf))
            with self.assertRaises(AssertionError):m.validate(*args)

    def test_post_review_cheap_performance_substitution_rejects(self):
        with tempfile.TemporaryDirectory() as t:
            args=self.fixture(Path(t));perf=json.loads(args[2].read_text());perf['draw_calls']=0;args[2].write_text(json.dumps(perf))
            with self.assertRaises(AssertionError):m.validate(*args)

    def test_transported_relative_raw_path(self):
        with tempfile.TemporaryDirectory() as t:
            args=self.fixture(Path(t));record=json.loads(args[0].read_text());record['raw_output_path']='specialist-review/raw.json';args[0].write_text(json.dumps(record))
            self.assertTrue(m.validate(*args)['passed'])
