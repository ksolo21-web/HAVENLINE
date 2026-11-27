import copy
import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from specialist_critic_runner import evaluate_group, review_phase, response_schema, response_bounds_errors

class ResponseBoundsTests(unittest.TestCase):
    def test_t10_schema_preserves_all_fields_without_forcing_pass_scores(self):
        schema=response_schema('T10',['one','two'])
        required={'observations','defects','coverage_complete','confidence','scores'}
        self.assertEqual(required,set(schema['required']))
        self.assertEqual(required,set(schema['properties']))
        self.assertNotIn('oneOf',schema)
        self.assertEqual(schema['properties']['scores']['required'],['one','two'])
        self.assertEqual(schema['properties']['scores']['properties']['one'],{'type':'number','minimum':0,'maximum':10})
        self.assertEqual(schema['properties']['observations'],{'type':'array','items':{'type':'string','maxLength':160},'minItems':2,'maxItems':2})
        self.assertEqual(schema['properties']['defects']['maxItems'],5)
        self.assertEqual(schema['properties']['defects']['items']['maxLength'],160)
        self.assertFalse(schema['additionalProperties'])

    def test_other_tasks_unchanged(self):
        for task in ['T09','T11',None]:
            schema=response_schema(task,['a'])
            self.assertEqual(schema['properties']['observations'],{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5})
            self.assertEqual(schema['properties']['defects'],{'type':'array','items':{'type':'string'},'maxItems':5})
            self.assertNotIn('oneOf',schema)
            self.assertEqual(response_bounds_errors(task,{}),[])
    def test_hostile_response_bounds(self):
        valid={'observations':['a'*160,'b'],'defects':['c'*160]*5}
        self.assertEqual(response_bounds_errors('T10',valid),[])
        for field,values in [('observations',[]),('observations',['a']),('observations',['a']*3),('observations',['a'*161,'b']),('observations',[1,'b']),('observations',None),('defects',['a']*6),('defects',['a'*161]),('defects',[{}]),('defects','bad')]:
            broken=copy.deepcopy(valid);broken[field]=values
            self.assertTrue(response_bounds_errors('T10',broken),(field,values))
        self.assertTrue(response_bounds_errors('T10',{}))
    def test_t10_low_score_can_honestly_report_missing_evidence_without_invented_defect(self):
        from reference_acceptance import record_errors
        for score in (0,9.0,9.5,9.99):
            review={'observations':['Only one view supplied.','Motion cycle missing.'],
                    'scores':{'one':score},'defects':[], 'coverage_complete':False}
            self.assertEqual([],response_bounds_errors('T10',review))
            self.assertTrue(record_errors(review,['one'],'C3',require_binding=False))

    def test_runner_uses_frozen_reference_dimensions_even_when_reviewer_omits_them(self):
        review={'scores':{'pacing':9.5},'coverage_complete':True,'defects':[]}
        self.assertEqual([],evaluate_group(review,['pacing'],'C7',[]))
        self.assertTrue(evaluate_group(review,['pacing'],'C7',['pacing']))
        self.assertNotIn('reference_sensitive_dimensions',review)

    def test_static_motion_runner_is_explicitly_interim(self):
        self.assertEqual('interim',review_phase('C5'))
        self.assertEqual('final',review_phase('C3'))
        from reference_acceptance import acceptance_binding,record_errors
        record={'scores':{'full_cycle':10},'coverage_complete':True,'defects':[],
                'reference_acceptance':acceptance_binding(review_phase('C5')),'approval_allowed':False,
                'status':'INTERIM_REVIEW_ONLY'}
        self.assertTrue(record_errors(record,['full_cycle'],'C5'))

class RequestRetentionTests(unittest.TestCase):
    def run_request(self, text, image=False):
        import base64, io, json, tempfile, types
        from unittest.mock import patch
        import specialist_critic_runner as runner
        # Deterministic image bytes isolate transport identity without installing
        # an image codec in the governance-only unit-test job.
        encoded_image=b'unit-test-image-bytes-preserved-verbatim'
        class ImageFixture:
            def convert(self,*a): return self
            def thumbnail(self,*a): pass
            def save(self,buffer,**kw): buffer.write(encoded_image)
        image_module=types.SimpleNamespace(Image=types.SimpleNamespace(open=lambda p:ImageFixture(),Resampling=types.SimpleNamespace(LANCZOS=1)))
        response={'choices':[{'finish_reason':'stop','message':{'content':'{"observations":["a","b"]}'}}]}
        captured=[]
        def urlopen(request,timeout):
            captured.append(request.data)
            self.assertEqual(timeout,1200)
            return io.BytesIO(json.dumps(response).encode())
        with tempfile.TemporaryDirectory() as directory, patch('specialist_critic_runner.urllib.request.urlopen',side_effect=urlopen), patch.dict(sys.modules,{'PIL':image_module}):
            path=pathlib.Path(directory)
            runner.request_local('fixture.jpg' if image else None,text,'prompt',runner.response_schema('T10',['a']),path,'group')
            retained=(path/'group-request.json').read_bytes()
            self.assertEqual(retained,captured[0])
            body=json.loads(retained)
            self.assertEqual(body['messages'][0]['content'][-1]['text'],'prompt\n\nSOURCE-BOUND STRUCTURED EVIDENCE:\n'+text)
            self.assertEqual(body['max_tokens'],900)
            if image:
                url=body['messages'][0]['content'][0]['image_url']['url']
                self.assertEqual(base64.b64decode(url.split(',',1)[1]),encoded_image)
            return retained
    def test_full_large_request_and_encoded_image_preserved(self):
        retained=self.run_request('evidence '*40000,image=True)
        self.assertGreater(len(retained),250000)
    def test_short_request_exactness(self):
        self.assertLess(len(self.run_request('small evidence')),250000)
    def test_write_and_network_failure_fail_closed(self):
        import tempfile
        from unittest.mock import patch
        import specialist_critic_runner as runner
        with tempfile.TemporaryDirectory() as directory:
            path=pathlib.Path(directory)
            with patch('pathlib.Path.write_bytes',side_effect=OSError('disk failed')), patch('specialist_critic_runner.urllib.request.urlopen') as network:
                with self.assertRaises(OSError):runner.request_local(None,'text','prompt',{},path,'write')
                network.assert_not_called()
            with patch('specialist_critic_runner.urllib.request.urlopen',side_effect=OSError('network failed')):
                with self.assertRaises(OSError):runner.request_local(None,'text','prompt',{},path,'network')
                self.assertTrue((path/'network-request.json').is_file())
                self.assertFalse((path/'network-raw.json').exists())
