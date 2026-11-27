from __future__ import annotations
import hashlib,json,pathlib,sys,tempfile,unittest
PRODUCTION=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PRODUCTION))
import critic_harness,closure_validator
from reference_acceptance import acceptance_binding
from lib import ROOT,DOCS,load_json,sha256_file

CANDIDATE='a'*40


class PerformanceReviewTransportTests(unittest.TestCase):
    def fixture(self,root,*,source_kind='agent_native',bad_metric=None,score=9.6):
        metrics={key:1 for key in ('visible_triangles','draw_calls','materials_visible','texture_gpu_memory_mb',
            'process_memory_mb','physics_active_bodies','animated_rigs_active','npc_companion_active_population',
            'storage_download_mb','cpu_frame_ms')}
        metrics['candidate_commit']=CANDIDATE
        if bad_metric=='missing':metrics.pop('cpu_frame_ms')
        elif bad_metric=='nan':metrics['draw_calls']=float('nan')
        performance=root/'performance.json';performance.write_text(json.dumps(metrics))
        index=root/'complete-index.json';index.write_text(json.dumps({'task_id':'T10','candidate_commit':CANDIDATE,'reference_sensitive_dimensions':{'C6':[]}}))
        items=[{'path':str(performance.relative_to(ROOT)),'sha256':sha256_file(performance),'kind':'json',
            'category':'performance_measurement','description':'Explicit unit test measured supplement'},
            {'path':str(index.relative_to(ROOT)),'sha256':sha256_file(index),'kind':'json',
            'category':'complete_evidence_index','description':'Explicit unit test input index'}]
        manifest={'task_id':'T10','critic_id':'C6','candidate_commit':CANDIDATE,'reference_sensitive_dimensions':[],
            'builder_identity':'unit-test-builder','independent_reviewer_identity':'unit-test-model-reviewer',
            'complete_evidence_index_sha256':sha256_file(index),'groups':[{'id':'performance','items':items}]}
        manifest_path=root/'input.json';manifest_path.write_text(json.dumps(manifest))
        dims=load_json(DOCS/'CRITIC_EXECUTION.json')['critics']['C6']['dimensions']
        original={'task_id':'T10','critic_id':'C6','candidate_hash':CANDIDATE,'input_manifest_hash':sha256_file(manifest_path),
            'complete_evidence_index_sha256':sha256_file(index),'reference_acceptance':acceptance_binding(),
            'reference_sensitive_dimensions':[],'scores':{name:score for name in dims},'defects':[],
            'coverage_complete':True,'confidence':'high','independent_runtime':True,'passed':True,'status':'PASS',
            'reviewed_evidence':items,'measured_supplement':{'path':str(performance.relative_to(ROOT)),'sha256':sha256_file(performance)}}
        session={'transport_kind':'performance_review_v1','source_kind':source_kind,'reviewer':{'kind':'agent_model',
            'identity':'unit-test-model-reviewer','independent':True,'provider':'unit-test-provider',
            'model':'unit-test-no-live-model','request_or_run_id':'unit-test/original-session'},'review':original}
        if source_kind=='api_request_response':
            request=root/'request.json';request.write_text(json.dumps({'candidate_hash':CANDIDATE,
                'input_manifest_hash':sha256_file(manifest_path),'actual_test_metrics':metrics}))
            response=root/'response.json';response.write_text(json.dumps({key:original[key] for key in ('scores','defects','coverage_complete','confidence')}))
            session['api_transport']={'request_path':str(request.relative_to(ROOT)),'request_sha256':sha256_file(request),
                'response_path':str(response.relative_to(ROOT)),'response_sha256':sha256_file(response)}
        session_path=root/'original-session.json';session_path.write_text(json.dumps(session))
        return manifest_path,session_path,performance,original

    def test_native_and_api_original_review_producer_consumer_preserve_scores_and_source_bytes(self):
        for kind in ('agent_native','api_request_response'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory(dir=ROOT) as directory:
                root=pathlib.Path(directory);manifest,session,performance,original=self.fixture(root,source_kind=kind)
                original_bytes=session.read_bytes()
                result=critic_harness.ingest_performance_review(manifest,session,root/'out',CANDIDATE)
                self.assertTrue(result['passed'],result['errors'])
                self.assertEqual(original['scores'],result['record']['scores'])
                self.assertTrue(all(value==9.6 for value in result['record']['scores'].values()))
                self.assertEqual(original_bytes,session.read_bytes())
                self.assertEqual(original['measured_supplement']['sha256'],sha256_file(performance))
                path=ROOT/result['record_path'];record=result['record']
                raw={key:record[key] for key in ('task_id','critic_id','scores','defects','coverage_complete','confidence',
                    'reference_acceptance','reference_sensitive_dimensions','provider','model','request_or_run_id','complete_evidence_index_sha256')}
                raw.update(candidate_commit=CANDIDATE,review_transport={'kind':'scored_performance_review_v1',
                    'critic_record_path':str(path.relative_to(ROOT)),'critic_record_sha256':sha256_file(path)})
                self.assertEqual([],closure_validator.validate_original_review_transport(raw))
                with self.assertRaises(ValueError):critic_harness.ingest_performance_review(manifest,session,root/'out',CANDIDATE)

    def test_missing_nan_or_substituted_measurements_block_original_high_scoring_review(self):
        for defect in ('missing','nan','substituted','missing_file'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory(dir=ROOT) as directory:
                root=pathlib.Path(directory);manifest,session,performance,_=self.fixture(root,bad_metric=defect)
                if defect=='substituted':performance.write_text(json.dumps({'candidate_commit':'b'*40,'cpu_frame_ms':1}))
                elif defect=='missing_file':performance.unlink()
                result=critic_harness.ingest_performance_review(manifest,session,root/'out',CANDIDATE)
                self.assertFalse(result['passed'],result)

    def test_measured_pass_cannot_invent_or_increase_original_scores(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=pathlib.Path(directory);manifest,session,performance,original=self.fixture(root,score=9.49)
            self.assertTrue(critic_harness.c6(performance,CANDIDATE)['passed'])
            result=critic_harness.ingest_performance_review(manifest,session,root/'out',CANDIDATE)
            self.assertFalse(result['passed']);self.assertEqual(original['scores'],result['record']['scores'])
            self.assertTrue(all(value==9.49 for value in result['record']['scores'].values()))

    def test_score_only_terminal_c6_transport_cannot_bypass_measurements(self):
        self.assertTrue(closure_validator.validate_original_review_transport({'critic_id':'C6',
            'review_transport':{'kind':'automated_request_response_v1'}}))
        self.assertTrue(closure_validator.validate_original_review_transport({'critic_id':'C6',
            'review_transport':{'kind':'external_independent_review_v1'}}))


if __name__=='__main__':unittest.main()
