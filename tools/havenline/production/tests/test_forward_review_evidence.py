from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PRODUCTION=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PRODUCTION))
import critic_harness
import closure_validator
import reference_acceptance as acceptance
from lib import ROOT,DOCS,load_json,sha256_file

CANDIDATE='a'*40


class ExternalReviewEvidenceTests(unittest.TestCase):
    def external(self,root,cid):
        from PIL import Image
        spec=load_json(DOCS/'CRITIC_EXECUTION.json')['critics'][cid]
        items=[]
        for name,color,camera in [('front','red','front'),('side','blue','side')]:
            if cid=='C5':
                file=root/(name+'.mp4')
                subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c='+color+':s=32x32:r=10',
                    '-t','1','-pix_fmt','yuv420p','-y',str(file)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                kind='video';category='motion_cycle' if name=='front' else 'motion_transition'
            else:
                file=root/(name+'.png');Image.new('RGB',(32,32),color).save(file)
                kind='image';category='candidate_geometry'
            items.append({'path':str(file.relative_to(ROOT)),'sha256':sha256_file(file),'kind':kind,
                'category':category,'camera':camera,'role':'candidate','description':'Unit test media only'})
        if cid=='C1':
            for rid in ('A','B'):
                file=root/('reference-'+rid+'.png');Image.new('RGB',(32,32),'green' if rid=='A' else 'yellow').save(file)
                items.append({'path':str(file.relative_to(ROOT)),'sha256':sha256_file(file),'kind':'image',
                    'category':'locked_reference','role':'reference','reference_id':rid,'description':'Unit test reference only'})
        if cid=='C5':
            file=root/'contact.png';Image.new('RGB',(32,32),'white').save(file)
            items.append({'path':str(file.relative_to(ROOT)),'sha256':sha256_file(file),'kind':'image',
                'category':'contact_detail','camera':'contact-close','role':'candidate','description':'Unit test contact only'})
        manifest={'task_id':'T09','critic_id':cid,'candidate_commit':CANDIDATE,'reference_sensitive_dimensions':[],
            'builder_identity':'unit-test-builder','independent_reviewer_identity':'unit-test-separate-reviewer',
            'complete_evidence_index_sha256':'e'*64,'groups':[{'id':'actual-media','items':items}]}
        manifest_path=root/'input.json';manifest_path.write_text(json.dumps(manifest))
        record={'task_id':'T09','critic_id':cid,'candidate_hash':CANDIDATE,'input_manifest_path':str(manifest_path.relative_to(ROOT)),
            'input_manifest_hash':sha256_file(manifest_path),'complete_evidence_index_sha256':'e'*64,
            'provider':'unit-test-native-review','model':'unit-test-no-model-run','request_or_run_id':'unit-test/separate-session',
            'reference_acceptance':acceptance.acceptance_binding(),'reference_sensitive_dimensions':[],
            'scores':{dim:10 for dim in spec['dimensions']},'defects':[],'coverage_complete':True,'confidence':'high',
            'independent_runtime':True,'passed':True,'status':'PASS'}
        review={**record,'reviewed_evidence':items,'pixel_review_complete':True}
        if cid=='C5':
            review['reviewed_ranges']=[{'path':item['path'],'sha256':item['sha256'],'start_seconds':0,
                'end_seconds':1,'checks':spec['dimensions']} for item in items if item['kind']=='video']
        session={'transport_kind':'external_independent_review_v1','reviewer':{'kind':'agent_model','identity':'unit-test-separate-reviewer',
            'independent':True,**{key:record[key] for key in ('provider','model','request_or_run_id')}},'review':review}
        session_path=root/'session.json';session_path.write_text(json.dumps(session))
        raw={**record,'format':'havenline-external-independent-review-v1','review_transport':{
            'kind':'external_independent_review_v1','session_path':str(session_path.relative_to(ROOT)),'session_sha256':sha256_file(session_path)}}
        raw_path=root/'raw.json';raw_path.write_text(json.dumps(raw))
        record.update(raw_output_path=str(raw_path.relative_to(ROOT)),raw_output_hash=sha256_file(raw_path))
        record_path=root/'critic-record.json';record_path.write_text(json.dumps(record))
        return record_path,session,items

    def rewrite_session(self,path,session):
        record=json.loads(path.read_text());raw_path=ROOT/record['raw_output_path'];raw=json.loads(raw_path.read_text())
        session_path=ROOT/raw['review_transport']['session_path'];session_path.write_text(json.dumps(session))
        raw['review_transport']['session_sha256']=sha256_file(session_path);raw_path.write_text(json.dumps(raw))
        record['raw_output_hash']=sha256_file(raw_path);path.write_text(json.dumps(record))

    def test_current_c1_c2_external_reviews_accept_real_decoded_media_and_native_session(self):
        for cid in ('C1','C2'):
            with self.subTest(critic=cid),tempfile.TemporaryDirectory(dir=ROOT) as directory:
                path,session,_=self.external(pathlib.Path(directory),cid)
                result=critic_harness.validate_raw(path,cid,CANDIDATE)
                self.assertTrue(result['passed'],result['errors'])
                self.assertNotIn('request_path',session)

    def test_camera_labels_cannot_turn_duplicate_candidate_bytes_into_distinct_views(self):
        for cid in ('C1','C2'):
            with self.subTest(critic=cid),tempfile.TemporaryDirectory(dir=ROOT) as directory:
                path,session,items=self.external(pathlib.Path(directory),cid)
                self.assertTrue(critic_harness.validate_raw(path,cid,CANDIDATE)['passed'])
                candidates=[item for item in items if item.get('role')=='candidate']
                first=ROOT/candidates[0]['path'];second=ROOT/candidates[1]['path']
                second.write_bytes(first.read_bytes());candidates[1]['sha256']=sha256_file(second)
                record=json.loads(path.read_text());manifest_path=ROOT/record['input_manifest_path']
                manifest=json.loads(manifest_path.read_text());manifest['groups'][0]['items']=items
                manifest_path.write_text(json.dumps(manifest));manifest_hash=sha256_file(manifest_path)
                record['input_manifest_hash']=manifest_hash
                raw_path=ROOT/record['raw_output_path'];raw=json.loads(raw_path.read_text());raw['input_manifest_hash']=manifest_hash
                raw_path.write_text(json.dumps(raw));record['raw_output_hash']=sha256_file(raw_path);path.write_text(json.dumps(record))
                session['review']['input_manifest_hash']=manifest_hash;session['review']['reviewed_evidence']=items
                self.rewrite_session(path,session)
                result=critic_harness.validate_raw(path,cid,CANDIDATE)
                self.assertFalse(result['passed'],result)
                self.assertTrue(any('duplicate candidate capture bytes' in error for error in result['errors']))

    def test_current_external_c5_requires_complete_actual_playback_ranges(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path,session,_=self.external(pathlib.Path(directory),'C5')
            result=critic_harness.validate_raw(path,'C5',CANDIDATE)
            self.assertTrue(result['passed'],result['errors'])
            for alteration in ('missing','short','checks','gap'):
                broken=copy.deepcopy(session)
                if alteration=='missing':broken['review'].pop('reviewed_ranges')
                elif alteration=='short':broken['review']['reviewed_ranges'][0]['end_seconds']=0.4
                elif alteration=='checks':
                    for row in broken['review']['reviewed_ranges']:row['checks']=['full_cycle']
                else:broken['review']['reviewed_ranges'][0]['start_seconds']=0.3
                self.rewrite_session(path,broken)
                result=critic_harness.validate_raw(path,'C5',CANDIDATE)
                with self.subTest(case=alteration):self.assertFalse(result['passed'],result)

    def test_original_session_cannot_disagree_or_be_the_builder(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path,session,_=self.external(pathlib.Path(directory),'C2')
            for key,value in [('coverage_complete',False),('scores',{'geometry_contact':7}),('passed',False)]:
                broken=copy.deepcopy(session);broken['review'][key]=value;self.rewrite_session(path,broken)
                result=critic_harness.validate_raw(path,'C2',CANDIDATE)
                with self.subTest(field=key):self.assertFalse(result['passed'])
            broken=copy.deepcopy(session);broken['reviewer']['identity']='unit-test-builder';self.rewrite_session(path,broken)
            result=critic_harness.validate_raw(path,'C2',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('distinct' in error for error in result['errors']))

    def test_human_signoff_cannot_waive_required_independent_model_lane(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path,session,_=self.external(pathlib.Path(directory),'C2')
            session['reviewer']['kind']='human';self.rewrite_session(path,session)
            result=critic_harness.validate_raw(path,'C2',CANDIDATE)
            self.assertFalse(result['passed']);self.assertTrue(any('human owner signoff is supplemental' in message for message in result['errors']))

    def test_internally_consistent_nonfinal_or_invalid_boolean_disposition_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=pathlib.Path(directory)
            for field,value in [('status','PENDING'),('status','fail'),('status','UNKNOWN'),('passed',0),
                                ('passed',None),('passed','false'),('approval_allowed',0)]:
                path,session,_=self.external(root,'C2');session['review'][field]=value
                record=json.loads(path.read_text());raw_path=ROOT/record['raw_output_path'];raw=json.loads(raw_path.read_text())
                record[field]=value;raw[field]=value;raw_path.write_text(json.dumps(raw));record['raw_output_hash']=sha256_file(raw_path);path.write_text(json.dumps(record))
                self.rewrite_session(path,session)
                result=critic_harness.validate_raw(path,'C2',CANDIDATE)
                with self.subTest(field=field,value=value):self.assertFalse(result['passed'],result)

    def test_external_or_static_specialist_format_cannot_bypass_deterministic_critics(self):
        for cid in ('C6','C9'):
            with self.subTest(critic=cid),tempfile.TemporaryDirectory(dir=ROOT) as directory:
                path,session,_=self.external(pathlib.Path(directory),cid)
                result=critic_harness.validate_raw(path,cid,CANDIDATE)
                self.assertFalse(result['passed']);self.assertTrue(any('no supported source-bound forward report' in message for message in result['errors']))
                record=json.loads(path.read_text());raw_path=ROOT/record['raw_output_path'];raw=json.loads(raw_path.read_text())
                raw['format']='havenline-specialist-report-v2';raw_path.write_text(json.dumps(raw))
                record['raw_output_hash']=sha256_file(raw_path);path.write_text(json.dumps(record))
                result=critic_harness.validate_raw(path,cid,CANDIDATE)
                self.assertFalse(result['passed']);self.assertTrue(any('no supported source-bound forward report' in message for message in result['errors']))

    def test_motion_metadata_or_fake_video_bytes_cannot_substitute_for_decoded_media(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=pathlib.Path(directory);fake=root/'fake.mp4';fake.write_text('claimed 60fps video, but no video bytes')
            item={'path':str(fake.relative_to(ROOT)),'sha256':sha256_file(fake),'category':'motion_cycle','camera':'front'}
            review={'reviewed_ranges':[{'path':item['path'],'sha256':item['sha256'],'start_seconds':0,'end_seconds':1,'checks':['full_cycle']}]}
            failures=acceptance.playback_errors(review,[item])
            self.assertTrue(any('cannot be fully decoded' in failure for failure in failures))

    def test_external_transport_is_usable_in_current_terminal_raw_gate(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path,_,_=self.external(pathlib.Path(directory),'C2');record=json.loads(path.read_text())
            raw={key:record[key] for key in ('task_id','critic_id','scores','defects','coverage_complete','confidence',
                'reference_acceptance','reference_sensitive_dimensions','provider','model','request_or_run_id','complete_evidence_index_sha256')}
            raw.update(candidate_commit=CANDIDATE,review_transport={'kind':'external_independent_review_v1',
                'critic_record_path':str(path.relative_to(ROOT)),'critic_record_sha256':sha256_file(path)})
            self.assertEqual([],closure_validator.validate_original_review_transport(raw))
            raw['complete_evidence_index_sha256']='f'*64
            self.assertTrue(closure_validator.validate_original_review_transport(raw))

    def test_transport_normalizer_cannot_relabel_the_original_complete_evidence_index(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path,_,_=self.external(pathlib.Path(directory),'C2');record=json.loads(path.read_text())
            record['complete_evidence_index_sha256']='f'*64
            path.write_text(json.dumps(record))
            result=critic_harness.validate_raw(path,'C2',CANDIDATE)
            self.assertFalse(result['passed'])
            self.assertTrue(any('complete evidence index' in message or 'complete_evidence_index_sha256' in message for message in result['errors']))
            raw={key:record[key] for key in ('task_id','critic_id','scores','defects','coverage_complete','confidence',
                'reference_acceptance','reference_sensitive_dimensions','provider','model','request_or_run_id','complete_evidence_index_sha256')}
            raw.update(candidate_commit=CANDIDATE,review_transport={'kind':'external_independent_review_v1',
                'critic_record_path':str(path.relative_to(ROOT)),'critic_record_sha256':sha256_file(path)})
            self.assertTrue(closure_validator.validate_original_review_transport(raw))


class TerminalAuthorityTests(unittest.TestCase):
    def test_current_c9_producer_binds_task_and_index_before_attacks_and_terminal_validation(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=pathlib.Path(directory);index=root/'index.json';index.write_text(json.dumps({'task_id':'T09','candidate_commit':CANDIDATE}))
            out=root/'security'
            command=[sys.executable,str(PRODUCTION/'security_exploit_harness.py'),'--candidate',CANDIDATE,
                '--task','T09','--evidence-index',str(index.relative_to(ROOT)),'--out',str(out.relative_to(ROOT)),
                '--adapter',sys.executable+' tools/havenline/production/tests/security_mock_adapter.py']
            process=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            self.assertEqual(0,process.returncode,process.stdout)
            path=out/'critic-record.json';record=json.loads(path.read_text())
            self.assertEqual(sha256_file(index),record['complete_evidence_index_sha256'])
            raw={key:record[key] for key in ('task_id','critic_id','scores','defects','coverage_complete','confidence',
                'reference_acceptance','reference_sensitive_dimensions','provider','model','request_or_run_id','complete_evidence_index_sha256')}
            raw.update(candidate_commit=CANDIDATE,review_transport={'kind':'deterministic_security_harness_v1',
                'critic_record_path':str(path.relative_to(ROOT)),'critic_record_sha256':sha256_file(path)})
            self.assertEqual([],closure_validator.validate_original_review_transport(raw))
            # A new index cannot be attached to a completed attack run afterwards.
            record['complete_evidence_index_sha256']='f'*64;path.write_text(json.dumps(record))
            raw['complete_evidence_index_sha256']='f'*64;raw['review_transport']['critic_record_sha256']=sha256_file(path)
            self.assertTrue(closure_validator.validate_original_review_transport(raw))
            raw['review_transport']={'kind':'automated_request_response_v1'}
            self.assertTrue(closure_validator.validate_original_review_transport(raw))

    def test_original_automated_failed_interim_or_historical_disposition_cannot_be_normalized_to_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=pathlib.Path(directory);request=root/'request.json';response=root/'response.json'
            raw={'critic_id':'C2','candidate_commit':CANDIDATE,'input_manifest_sha256':'e'*64,
                'scores':{'geometry_contact':10},'coverage_complete':True,'defects':[],'confidence':'high',
                'reference_sensitive_dimensions':[]}
            request.write_text(json.dumps({'candidate':CANDIDATE,'input_manifest_sha256':'e'*64}))
            base={key:raw[key] for key in ('scores','coverage_complete','defects','confidence')}
            for extra in ({'passed':False},{'passed':0},{'passed':None},{'passed':'false'},{'status':'FAIL'},
                          {'status':'PENDING'},{'status':'fail'},{'approval_allowed':False},{'approval_allowed':0},{'review_scope':'historical'},
                          {'reference_acceptance':acceptance.acceptance_binding('interim')}):
                response.write_text(json.dumps({**base,**extra}))
                raw['review_transport']={'kind':'automated_request_response_v1','request_path':str(request.relative_to(ROOT)),
                    'request_sha256':sha256_file(request),'response_path':str(response.relative_to(ROOT)),'response_sha256':sha256_file(response)}
                with self.subTest(disposition=extra):self.assertTrue(closure_validator.validate_original_review_transport(raw))

    def test_effective_dependency_rejection_overrides_graph_approved(self):
        graph={'tasks':{'T12':{'dependencies':['T11']},'T11':{'status':'APPROVED'}}}
        with patch.object(closure_validator,'effective_approval',return_value={'passed':False,'effective_approved':False,'errors':['owner visual rejection']}):
            failures=closure_validator.forward_dependency_errors('T12','b'*40,graph)
        self.assertTrue(any('not effectively approved' in failure for failure in failures))
        with patch.object(closure_validator,'effective_approval',return_value={'passed':True,'effective_approved':True,'errors':[]}):
            self.assertEqual([],closure_validator.forward_dependency_errors('T12','b'*40,graph))

    def test_current_invalidation_and_owner_signoff_rejection_block_terminal_gate(self):
        with patch.object(closure_validator,'active_invalidation',return_value={'status':'ACTIVE'}),patch.object(closure_validator,'validate_signoff',return_value={'passed':True,'errors':[]}):
            self.assertTrue(closure_validator.forward_visual_errors('T09',CANDIDATE,True,['C1','C5']))
        with patch.object(closure_validator,'active_invalidation',return_value=None),patch.object(closure_validator,'validate_signoff',return_value={'passed':False,'errors':['user explicitly rejected final visual reference fidelity']}):
            self.assertTrue(closure_validator.forward_visual_errors('T09',CANDIDATE,True,['C1','C5']))
        with patch.object(closure_validator,'active_invalidation',return_value=None),patch.object(closure_validator,'validate_signoff',return_value={'passed':True,'approval_allowed':False,'historical_only':True,'errors':[]}):
            self.assertTrue(closure_validator.forward_visual_errors('T09',CANDIDATE,True,['C1','C5']))
        with patch.object(closure_validator,'active_invalidation',return_value=None),patch.object(closure_validator,'validate_signoff',return_value={'passed':True,'errors':[]}) as signoff:
            self.assertEqual([],closure_validator.forward_visual_errors('T09',CANDIDATE,False,['C5']))
            signoff.assert_called_once_with('T09',CANDIDATE)


if __name__=='__main__':unittest.main()
