"""Synthetic validator regression fixtures; never production/art/device evidence."""
import copy, importlib.util,json,tempfile,unittest
from pathlib import Path

s=importlib.util.spec_from_file_location('closure',Path(__file__).with_name('validate_task01_completion.py'))
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class ClosureValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.spec={}
        for role in sorted(v.ROLES):
            for index,groups in enumerate([['variant-1','clearance'],['variant-2','forest'],['variant-3','camera-motion']]):
                p=self.root/f'{role}-{index}';p.mkdir()
                rows=[]
                for group in groups:
                    review={'observations':['SYNTHETIC UNIT FIXTURE','NOT AN ART VERDICT'],'defects':[],'coverage_complete':True,'confidence':'high','scores':{k:9.1 for k in v.KEYS}}
                    row={'task':'T01','source':v.SOURCE,'role':role,'group':group,'independent_execution':True,'competency_passed':True,'passed':True,'review':review,'lowest_score':9.1}
                    if group=='clearance':
                        review['evidence_facts']={'baseline_tree_blocks_central_player':False,'disabled_tree_blocks_central_player':True,'enabled_tree_blocks_central_player':False,'depleted_resource_tree_visible':False}
                        row['factual_image_recognition_passed']=True
                    rows.append(row)
                data={'source':v.SOURCE,'role':role,'shard':index,'reviews':rows,'competency_passed':True}
                self.spec[p]=data
        self.write()
    def tearDown(self):self.tmp.cleanup()
    def write(self):
        for p,data in self.spec.items():
            (p/'shard-review.json').write_text(json.dumps(data))
            (p/'competency.json').write_text(json.dumps({'passed':True,'answers':v.PROBE}))
            (p/'competency-raw.json').write_text(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(v.PROBE)}}]}))
            (p/'provenance.json').write_text(json.dumps({'source':v.SOURCE,'model':'Qwen/Qwen3.5-9B','model_revision':v.MODEL_REVISION,'competency_passed':True,'independent_model_execution':True}))
            for row in data['reviews']:
                (p/(row['group']+'-raw.json')).write_text(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(row['review'])}}]}))
    def first(self):return next(iter(self.spec.values()))['reviews'][0]
    def result(self):return v.check_reviews(self.root,v.SOURCE)
    def reject_after(self,mutator):mutator();self.write();self.assertTrue(self.result()[1])
    def test_synthetic_structure_valid_not_real_approval(self):
        rows,errors=self.result();self.assertEqual(len(rows),12);self.assertEqual(errors,[])
    def test_exact_nine_meets_intermediate_threshold(self):
        for d in self.spec.values():
            for r in d['reviews']:r['review']['scores']={k:9.0 for k in v.KEYS};r['lowest_score']=9.0
        self.write();self.assertFalse(self.result()[1])
    def test_below_nine(self):self.reject_after(lambda:self.first()['review']['scores'].update(materials=8.99))
    def test_nan(self):self.reject_after(lambda:self.first()['review']['scores'].update(materials=float('nan')))
    def test_bool_is_not_score(self):self.reject_after(lambda:self.first()['review']['scores'].update(materials=True))
    def test_ten_does_not_erase_defect(self):self.reject_after(lambda:self.first()['review'].update(scores={k:10 for k in v.KEYS},defects=['Unresolved mandatory fixture defect']))
    def test_reported_score_cannot_be_inflated(self):self.reject_after(lambda:self.first().update(lowest_score=10))
    def test_missing_dimension(self):self.reject_after(lambda:self.first()['review']['scores'].pop('materials'))
    def test_no_independent_execution(self):self.reject_after(lambda:self.first().update(independent_execution=False))
    def test_false_pass_flag(self):self.reject_after(lambda:self.first().update(passed=False))
    def test_stale_source(self):self.reject_after(lambda:self.first().update(source='f'*40))
    def test_low_confidence(self):self.reject_after(lambda:self.first()['review'].update(confidence='low'))
    def test_unreviewed_coverage(self):self.reject_after(lambda:self.first()['review'].update(coverage_complete=False))
    def test_duplicate_group(self):self.reject_after(lambda:next(iter(self.spec.values()))['reviews'][1].update(group='variant-1'))
    def test_raw_scores_mismatch(self):
        p=next(iter(self.spec));f=p/'variant-1-raw.json';a=json.loads(f.read_text());b=json.loads(a['choices'][0]['message']['content']);b['scores']['materials']=1;a['choices'][0]['message']['content']=json.dumps(b);f.write_text(json.dumps(a));self.assertTrue(self.result()[1])
    def test_raw_truncation(self):
        p=next(iter(self.spec));f=p/'variant-1-raw.json';a=json.loads(f.read_text());a['choices'][0]['finish_reason']='length';f.write_text(json.dumps(a));self.assertTrue(self.result()[1])
    def test_clearance_wrong_facts(self):
        def mutate():next(iter(self.spec.values()))['reviews'][1]['review']['evidence_facts']['enabled_tree_blocks_central_player']=True
        self.reject_after(mutate)
    def test_clearance_unverified(self):self.reject_after(lambda:next(iter(self.spec.values()))['reviews'][1].update(factual_image_recognition_passed=False))
    def test_missing_role(self):
        for p in self.root.glob('reference-fidelity-*'):(p/'shard-review.json').unlink()
        self.assertTrue(self.result()[1])
    def test_missing_raw(self):
        (next(iter(self.spec))/'variant-1-raw.json').unlink();self.assertTrue(self.result()[1])
    def test_false_blind_competency(self):self.reject_after(lambda:next(iter(self.spec.values())).update(competency_passed=False))
    def test_row_missing_blind_competency(self):self.reject_after(lambda:self.first().pop('competency_passed'))
    def test_missing_probe_raw(self):
        (next(iter(self.spec))/'competency-raw.json').unlink();self.assertTrue(self.result()[1])
    def test_incorrect_probe_raw(self):
        p=next(iter(self.spec))/'competency-raw.json';r=json.loads(p.read_text());r['choices'][0]['message']['content']=json.dumps(dict(v.PROBE,A='snow_tree'));p.write_text(json.dumps(r));self.assertTrue(self.result()[1])
    def test_unpinned_model_revision(self):
        p=next(iter(self.spec))/'provenance.json';r=json.loads(p.read_text());r['model_revision']='wrong';p.write_text(json.dumps(r));self.assertTrue(self.result()[1])
    def test_duplicate_shard_index(self):
        next(iter(self.spec.values()))['shard']=1;self.write();self.assertTrue(self.result()[1])
if __name__=='__main__':unittest.main(verbosity=2)
