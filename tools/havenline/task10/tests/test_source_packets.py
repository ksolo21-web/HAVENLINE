import copy,json,math,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import source_packets as m

class PacketTests(unittest.TestCase):
    def source(self):
        return (Path(__file__).resolve().parents[4]/m.SOURCE_PATH).read_text()
    def valid(self):
        return dict(observations=['Inspected source.', 'Inspected boundaries.'],defects=[],coverage_complete=True,confidence='high',scores={d:9.5 for d in m.DIMENSIONS})
    def test_lossless_actual_whole_file(self):
        source=self.source();header,units=m.split_functions(source)
        self.assertEqual(header+''.join(u['text'] for u in units.values()),source)
        self.assertEqual(37,len(units))
    def test_every_function_has_one_primary_assignment(self):
        plan=m.packets(self.source(),'a'*40,'b'*40)
        actual=[n for p in plan['groups'].values() for n in p['functions']]
        self.assertEqual(37,len(actual));self.assertEqual(37,len(set(actual)))
    def test_packet_does_not_cut_ground_projection(self):
        source=self.source();_,units=m.split_functions(source)
        p=m.packets(source,'a'*40,'b'*40)['groups']['lighting']['prompt']
        self.assertIn(units['_ground_shadow_point']['text'],p)
        self.assertIn(units['_projected_response_rect']['text'],p)
    def test_source_uses_real_newlines_not_json_escaped_code(self):
        plan=m.packets(self.source(),'a'*40,'b'*40)
        self.assertIn('\n\treturn',plan['groups']['lifecycle']['prompt'])
    def test_added_function_blocks_missing_coverage(self):
        with self.assertRaisesRegex(ValueError,'complete source coverage'):
            m.packets(self.source()+'\nfunc uncovered():\n\tpass\n','a'*40,'b'*40)
    def test_duplicate_function_blocks(self):
        with self.assertRaises(ValueError):m.split_functions('func a():\n\tpass\nfunc a():\n\tpass\n')
    def test_non_exact_source_identity_rejected(self):
        with self.assertRaises(ValueError):m.packets(self.source(),'main','b'*40)
    def test_valid_review(self):self.assertEqual([],m.result_errors(self.valid()))
    def test_exact_threshold_rejected(self):
        r=self.valid();r['scores'][m.DIMENSIONS[0]]=9.0
        self.assertTrue(m.result_errors(r))
    def test_unrounded_above_threshold_accepted(self):
        r=self.valid();r['scores'][m.DIMENSIONS[0]]=9.00001
        self.assertEqual([],m.result_errors(r))
    def test_every_numeric_failure_blocks(self):
        for v in [None,True,'10',0,8.9999,10.01,float('nan'),float('inf')]:
            with self.subTest(v=v):
                r=self.valid();r['scores'][m.DIMENSIONS[0]]=v;self.assertTrue(m.result_errors(r))
    def test_missing_and_extra_dimensions_rejected(self):
        for edit in ('missing','extra','empty'):
            r=self.valid()
            if edit=='missing':r['scores'].pop(m.DIMENSIONS[0])
            elif edit=='extra':r['scores']['another']=10
            else:r['scores']={}
            self.assertTrue(m.result_errors(r))
    def test_high_scores_cannot_hide_any_layer_findings(self):
        for layer in ('PRODUCT','EVIDENCE','TOOL'):
            r=self.valid();r['defects']=[{'layer':layer,'finding':'Source-bound unresolved finding.'}]
            self.assertTrue(m.result_errors(r))
    def test_incomplete_and_low_confidence_block(self):
        for change in [dict(coverage_complete=False),dict(coverage_complete=1),dict(confidence='low')]:
            r=self.valid();r.update(change);self.assertTrue(m.result_errors(r))
    def test_duplicate_json_keys_and_nonfinite_reject(self):
        for raw in ['{"a":1,"a":2}','{"x":NaN}','{"x":Infinity}','[]']:
            with self.assertRaises(ValueError):m.exact_json(raw)
    def test_empty_or_malformed_tokens_rejected(self):
        for tokens in [[],None,'tokens',[True],[1,'2']]:
            with self.assertRaises(ValueError):m.check_admission(tokens)
    def test_measured_packet_budget_is_fail_closed(self):
        self.assertEqual(4096,m.check_admission([1]*4096))
        with self.assertRaises(ValueError):m.check_admission([1]*4097)
    def test_malformed_classification_or_extra_fields_rejected(self):
        r=self.valid();r['defects']=[{'layer':'PASS','finding':'bad'}];self.assertTrue(m.result_errors(r))
        r=self.valid();r['extra']=True;self.assertTrue(m.result_errors(r))

if __name__=='__main__':unittest.main()
