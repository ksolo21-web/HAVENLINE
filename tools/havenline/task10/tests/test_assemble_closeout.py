"""Disposable synthetic interface rehearsal. No test records leave TemporaryDirectory.

Positive fixtures exercise serialization and the full assembler with a unittest-only
patch of diagnostic rejection, plus actual production CLI consumers. All fixture
provenance stays explicitly synthetic; no production bypass is implemented.
The public entry point explicitly rejects the same diagnostic provenance.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
import assemble_closeout as m
import export_closure_records as exporter
import test_export_closure_records as export_tests


class CloseoutTests(unittest.TestCase):
    def test_production_rejects_diagnostic_provenance_recursively(self):
        for value in ({'diagnostic_only': True}, {'nested': [{'provider': 'synthetic-test-provider'}]},
                      {'test_fixture': 'yes'}, {'fixture_only': True}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'diagnostic'):
                m.reject_diagnostic(value)

    def test_source_result_cannot_hide_failure(self):
        for value in ({'passed': True, 'candidate': 'b'*40}, {'passed': False, 'status': 'PASS', 'candidate': 'a'*40},
                      {'passed': True, 'candidate': 'a'*40, 'errors': ['failed']},
                      {'passed': True, 'candidate': 'a'*40, 'candidate_commit': 'b'*40}):
            with self.assertRaises(ValueError): m.source_pass(value, 'a'*40, 'proof')

    def test_reference_requires_original_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'proof.json'
            path.write_text('{"passed": true}')
            ref = {'path': str(path), 'sha256': m.digest(path.read_bytes())}
            self.assertEqual(m.read_reference(ref)[0], {'passed': True})
            path.write_text('{"passed": false}')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): m.read_reference(ref)

    def git(self, repo, *args):
        return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.PIPE).decode().strip()

    def test_bounded_zip_override_and_immutable_blob(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary)
            self.git(repo,'init','--quiet');self.git(repo,'config','user.name','Fixture')
            self.git(repo,'config','user.email','fixture@example.invalid')
            m.write(repo,'.gitattributes',b'*.zip filter=lfs diff=lfs merge=lfs -text\n')
            directory=repo/m.TASK/'ReviewExports'
            m.write(repo,m.TASK+'/ReviewExports/.gitattributes',b'*.zip -filter -diff -merge\n')
            m.write(repo,m.TASK+'/ReviewExports/original.zip',b'original archive bytes')
            self.git(repo,'add','.');self.git(repo,'commit','--quiet','-m','Diagnostic normal Git blob')
            m.verify_export_storage(repo)
            self.assertEqual(b'original archive bytes',subprocess.check_output(['git','show','HEAD:'+m.TASK+'/ReviewExports/original.zip'],cwd=repo))
            for contents in (b'*.zip -filter -diff -merge\n* -filter\n', b'*.zip filter=lfs\n'):
                (directory/'.gitattributes').write_bytes(contents)
                with self.assertRaisesRegex(ValueError,'exact task-owned'):m.verify_export_storage(repo)
            (directory/'.gitattributes').unlink()
            with self.assertRaises(OSError):m.verify_export_storage(repo)
            (directory/'.gitattributes').write_bytes(b'*.zip -filter -diff -merge\n')
            (directory/'original.zip').write_bytes(b'version https://git-lfs.github.com/spec/v1\n')
            self.git(repo,'add','.');self.git(repo,'commit','--quiet','-m','Diagnostic pointer mutation')
            with self.assertRaisesRegex(ValueError,'LFS pointer'):m.verify_export_storage(repo)
            with (directory/'original.zip').open('wb') as stream:stream.truncate(24*1024*1024+1)
            with self.assertRaisesRegex(ValueError,'24 MiB'):m.verify_export_storage(repo)
            m.write(repo,m.TASK+'/.gitattributes',b'*.zip -filter -diff -merge\n')
            with self.assertRaisesRegex(ValueError,'outside ReviewExports'):m.verify_export_storage(repo)

    def prepare_repo(self, target):
        repo = target / 'repo'
        subprocess.run(['git', 'clone', '--quiet', '--shared', str(m.ROOT), str(repo)], check=True)
        self.git(repo, 'remote', 'remove', 'origin')
        self.assertFalse(self.git(repo, 'remote'))
        self.git(repo, 'config', 'user.name', 'Disposable synthetic rehearsal')
        self.git(repo, 'config', 'user.email', 'fixture@example.invalid')
        # Include current uncommitted consumer repairs, only inside disposable repo.
        for directory in ('tools', 'Docs/Production', '.github/workflows'):
            shutil.copytree(m.ROOT / directory, repo / directory, dirs_exist_ok=True)
        docs = repo / 'Docs/Production'
        registry = m.load(docs / 'WORKSTREAM_REGISTRY.json')
        ws = next(r for r in registry['workstreams'] if r['task_id'] == 'T10')
        ws['status'] = 'UNDER_REVIEW'
        base = self.git(repo, 'rev-parse', 'HEAD')
        m.write(repo, 'Docs/Production/WORKSTREAM_REGISTRY.json', registry)
        graph = m.load(docs / 'DEPENDENCY_GRAPH.json'); graph['tasks']['T10']['status'] = 'UNDER_REVIEW'
        m.write(repo, 'Docs/Production/DEPENDENCY_GRAPH.json', graph)
        own = m.load(docs / 'PATH_OWNERSHIP.json')
        next(r for r in own['active_owners'] if r['task_id'] == 'T10')['status'] = 'UNDER_REVIEW'
        m.write(repo, 'Docs/Production/PATH_OWNERSHIP.json', own)
        self.git(repo, 'add', 'tools', 'Docs/Production', '.github/workflows')
        self.git(repo, 'commit', '--quiet', '-m', 'DIAGNOSTIC ONLY: disposable consumer rehearsal')
        return repo, base, self.git(repo, 'rev-parse', 'HEAD')

    def prepare_exports(self, target, repo, candidate):
        import zipfile
        records = target / 'reviews'; records.mkdir()
        payload, old_candidate = export_tests.FullReviewExportTests().prepare(records)
        for cid in m.CRITICS:
            manifest = json.loads(payload[cid + '-manifest.json'])
            manifest['candidate_commit'] = candidate
            if cid == 'C6':
                perf = json.loads(payload['performance.json']); perf['candidate_commit'] = candidate
                payload['performance.json'] = m.encoded(perf)
                manifest['groups'][0]['items'][0]['sha256'] = m.digest(payload['performance.json'])
            payload[cid + '-manifest.json'] = m.encoded(manifest)
            path = records / cid / 'critic-record.json'; record = m.load(path)
            raw_path = records / cid / 'raw-output.json'
            raw = json.loads(raw_path.read_text().replace(old_candidate, candidate))
            record['candidate_hash'] = candidate
            record['input_manifest_hash'] = m.digest(payload[cid + '-manifest.json'])
            if cid in ('C1', 'C2'): raw['input_manifest_hash'] = record['input_manifest_hash']
            raw_path.write_bytes(m.encoded(raw)); record['raw_output_hash'] = m.digest(raw_path.read_bytes())
            path.write_bytes(m.encoded(record))
        payload['progression.json'] = m.encoded(dict(candidate_commit=candidate, passed=True, checks=350, diagnostic_only=True))
        payload['runtime-provenance.json'] = m.encoded(dict(candidate_commit=candidate, **{key:'DIAGNOSTIC ONLY' for key in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH')}))
        payload['evidence-index.json'] = m.encoded(dict(candidate=candidate, files={k: m.digest(v) for k,v in payload.items()}))
        run = dict(id=123, head_sha=candidate, head_branch='codex/havenline-sequential-task-01', status='completed', conclusion='success')
        def archive(name, files, aid):
            path = target / (name + '.zip')
            with zipfile.ZipFile(path, 'w') as z:
                for key, value in files.items(): z.writestr(key, value)
            artifact = dict(id=aid, name=name, workflow_run=dict(id=123,head_sha=candidate), expired=False,
                size_in_bytes=path.stat().st_size, digest='sha256:'+m.digest(path.read_bytes()),
                created_at='2026-09-18T00:00:00Z', expires_at='2026-12-17T00:00:00Z')
            return path, artifact
        capture_zip, capture = archive('havenline-task10-critic-input-'+candidate, payload, 456)
        regression_zip, regression = archive('havenline-task10-first-milestone-'+candidate, {'regression.log': b'DIAGNOSTIC ONLY'}, 457)
        hosted = {}
        for i,cid in enumerate(('C3','C4','C7')):
            path, artifact = archive('havenline-task10-'+cid+'-'+candidate,
                {'specialist-review/'+p.name:p.read_bytes() for p in (records/cid).iterdir()}, 500+i)
            hosted[cid] = dict(archive=str(path),artifact=artifact)
        self.git(repo,'commit','--quiet','--allow-empty','-m','DIAGNOSTIC ONLY: later governance integration head')
        integration_head=self.git(repo,'rev-parse','HEAD')
        args = dict(candidate=candidate, integration_head=integration_head, archive=str(capture_zip),
                    regression_archive=str(regression_zip), records_root=str(records), out=str(repo))
        for key,value in [('run',run),('artifact',capture),('regression_run',run),('regression_artifact',regression),('hosted_artifacts',hosted)]:
            path=target/(key+'.json'); path.write_bytes(m.encoded(value)); args[key]=str(path)
        def execute():
            argv=[]
            for key,value in args.items(): argv.extend(['--'+key.replace('_','-'),value])
            return m.successful(m.run_cli(repo,'tools/havenline/task10/export_closure_records.py',*argv))
        reports=[execute()]
        # Disposable-only proposed fix: root/C0 owns authorization for real attrs.
        m.write(repo, m.TASK+'/ReviewExports/.gitattributes', b'*.zip -filter -diff -merge\n')
        self.git(repo,'add',m.TASK+'/ReviewExports')
        self.git(repo,'commit','--quiet','-m','DIAGNOSTIC ONLY: immutable synthetic originals')
        export_commit=self.git(repo,'rev-parse','HEAD');args['export_commit']=export_commit
        reports.append(execute())
        m.verify_export_storage(repo)
        return export_commit,reports,args

    def test_full_assembler_proposed_flow_with_disposable_diagnostic_boundary_patch(self):
        # The ONLY patched behavior is diagnostic provenance rejection, inside
        # this test process; no production bypass or reviewer score changes.
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='t10-synthetic-no-remote-') as temporary:
            target=Path(temporary);repo,base,candidate=self.prepare_repo(target)
            export_commit,reports,args=self.prepare_exports(target,repo,candidate)
            def reference(name,value):
                path=target/(name+'.json');path.write_bytes(m.encoded(value))
                return dict(path=str(path),sha256=m.digest(path.read_bytes()))
            spec=dict(candidate=candidate,base=base,integration_head=args['integration_head'],
                      export_commit=export_commit,approved_at='2026-09-18T00:00:00Z',
                      export_arguments={key:value for key,value in args.items() if key not in ('candidate','integration_head','export_commit','out')})
            c0=m.load(repo/m.TASK/'C0_ROOT_CAUSE.json')
            spec['c0_report']=dict(path=str(repo/m.TASK/'C0_ROOT_CAUSE.json'),sha256=m.digest((repo/m.TASK/'C0_ROOT_CAUSE.json').read_bytes()))
            proofs={f'G{i}':reference(f'gate-{i}',dict(candidate_commit=candidate,gate_id=f'G{i}',passed=True,diagnostic_only=True)) for i in range(1,15)}
            spec['gates']=reference('gates',dict(candidate_commit=candidate,gates={gate:dict(status='PASS',proofs=[ref]) for gate,ref in proofs.items()}))
            spec['path_validation']=reference('path',dict(candidate=candidate,base=base,passed=True,diagnostic_only=True))
            spec['tests']=reference('tests',dict(candidate_commit=candidate,passed=True,records=['DIAGNOSTIC ONLY'],diagnostic_only=True))
            spec['progression']=reference('progression',dict(candidate_commit=candidate,passed=True,checks=350,diagnostic_only=True))
            observation=dict(schema_version=1,passed=True,task_id='T10',source_sha=candidate,workflow_run_id=123,
                bundle_is_observation_not_authority=True,quality_thresholds_unchanged=True,environment_exact=True,environment_fingerprint='DIAGNOSTIC ONLY',
                environment_provenance=dict(candidate_commit=candidate,**{key:'DIAGNOSTIC ONLY' for key in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH')}),
                telemetry=dict(source_sha=candidate,task_id='T10',terminal_class='SUCCESS',**{k:0 for k in ('queue_seconds','run_seconds','gate_durations','rerun_count','c0_cycles','proof_cache_hits','artifact_bytes','terminal_gate')}),
                task_state=dict(task_id='T10',candidate_commit=candidate,snapshot_is_derived_not_authority=True),diagnostic_only=True)
            spec['factory_observation']=reference('factory',observation)
            actual_changes=set(self.git(repo,'diff','--name-only',c0['failed_candidate'],candidate).splitlines())
            bookkeeping={m.TASK+'/C0_ROOT_CAUSE.json',m.TASK+'/REPAIR_PLAN.json'}
            defects=[]
            for blocker in c0['blockers']:
                row=dict(id=blocker['id'],classification=blocker['classification'],status='VERIFIED_CLOSED',
                    affected_object=blocker['affected_object'],
                    causal_files=sorted((set(blocker['files_to_change']) & actual_changes)-bookkeeping),
                    command_or_gate='synthetic-test-command',reviewer_or_owner='synthetic-test-reviewer',
                    proof_candidate=candidate,unresolved=False)
                proof=dict(candidate_commit=candidate,passed=True,diagnostic_only=True,blocker_id=row['id'],
                           **{key:row[key] for key in ('affected_object','causal_files','command_or_gate','reviewer_or_owner')})
                row['verification_proofs']=[reference('defect-'+row['id'],proof)]
                defects.append(row)
            spec['defect_dispositions']=reference('dispositions',dict(candidate_commit=candidate,defects=defects,diagnostic_only=True))
            spec_path=target/'spec.json';spec_path.write_bytes(m.encoded(spec))
            # Unmodified real CLI must reject precisely these synthetic inputs.
            rejected=m.run_cli(repo,'tools/havenline/task10/assemble_closeout.py','--spec',spec_path,'--out',target/'rejected')
            self.assertNotEqual(rejected['exit_code'],0);self.assertIn('diagnostic',rejected['stdout'])
            self.assertFalse((target/'rejected').exists())
            with patch.object(m,'ROOT',repo),patch.object(m,'reject_diagnostic',lambda value:None):
                # Exercise the real public input contract with complete synthetic
                # provenance retained, not handcrafted canonical closure outputs.
                m.verify_inputs(spec)
                for label,key,mutate in [
                    ('missing gate','gates',lambda d:d['gates'].pop('G14')),
                    ('unbound gate','gates',lambda d:d['gates']['G1'].update(proofs=[])),
                    ('missing blocker','defect_dispositions',lambda d:d['defects'].pop()),
                    ('duplicate blocker','defect_dispositions',lambda d:d['defects'].append(copy.deepcopy(d['defects'][0]))),
                    ('unknown blocker','defect_dispositions',lambda d:d['defects'][0].update(id='unknown')),
                    ('unresolved blocker','defect_dispositions',lambda d:d['defects'][0].update(unresolved=True)),
                    ('stale proof','defect_dispositions',lambda d:d['defects'][0].update(proof_candidate='b'*40)),
                    ('missing causal proof','defect_dispositions',lambda d:d['defects'][0].update(causal_files=[])),
                    ('changed affected object','defect_dispositions',lambda d:d['defects'][0].update(affected_object='other object')),
                    ('foreign causal file','defect_dispositions',lambda d:d['defects'][0].update(causal_files=['HavenlineGodot/scripts/world_transform.gd'])),
                    ('duplicate causal file','defect_dispositions',lambda d:d['defects'][0]['causal_files'].append(d['defects'][0]['causal_files'][0])),
                    ('bookkeeping causal file','defect_dispositions',lambda d:d['defects'][0]['causal_files'].append(m.TASK+'/C0_ROOT_CAUSE.json')),
                    ('generic gate proof','defect_dispositions',lambda d:d['defects'][0].update(verification_proofs=[proofs['G1']])),
                    ('unrelated blocker proof','defect_dispositions',lambda d:d['defects'][0].update(verification_proofs=d['defects'][1]['verification_proofs'])),
                    ('command mismatch','defect_dispositions',lambda d:d['defects'][0].update(command_or_gate='unrelated command')),
                    ('reviewer mismatch','defect_dispositions',lambda d:d['defects'][0].update(reviewer_or_owner='unrelated reviewer'))]:
                    with self.subTest(label=label):
                        changed=copy.deepcopy(spec);value=m.load(spec[key]['path']);mutate(value)
                        changed[key]=reference('mutation-'+key,value)
                        with self.assertRaises(ValueError):m.verify_inputs(changed)
                unchanged=[(blocker,path) for blocker in c0['blockers'] for path in blocker['files_to_change'] if path not in actual_changes and path not in bookkeeping]
                self.assertTrue(unchanged,'fixture must exercise authorized-but-unchanged files')
                blocker,path=unchanged[0]
                changed=copy.deepcopy(spec);value=m.load(spec['defect_dispositions']['path'])
                next(row for row in value['defects'] if row['id']==blocker['id'])['causal_files'].append(path)
                changed['defect_dispositions']=reference('unchanged-causal-file',value)
                with self.assertRaisesRegex(ValueError,'actual authorized changes'):m.verify_inputs(changed)
                proposal=m.assemble(spec,target/'disposable-proposal')
            self.assertEqual('PROPOSED',proposal['status']);self.assertFalse(proposal['task_approved'])
            self.assertTrue(all(report['exit_code']==0 for report in proposal['consumers']))
            import os
            if os.environ.get('T10_REHEARSAL_REPORT'):
                path=Path(os.environ['T10_REHEARSAL_REPORT'])
                summary=m.load(path) if path.exists() else dict(diagnostic_only=True,production_approval=False)
                summary['full_assembler_flow']=dict(passed=True,unmodified_cli_rejected_synthetic=True,
                    unittest_only_patch='reject_diagnostic; no other validation patched',
                    distinct_assignment_and_integration_bases=True,distinct_candidate_and_governance_head=True,
                    consumers=[dict(command=r['command'],exit_code=r['exit_code'],stdout_sha256=m.digest(r['stdout'].encode())) for r in proposal['consumers']])
                path.write_bytes(m.encoded(summary))
            self.assertNotEqual(candidate,spec['integration_head'])
            staged=m.load(target/'disposable-proposal/overlay/Docs/Production/WORKSTREAM_REGISTRY.json')
            assigned=next(row for row in staged['workstreams'] if row['task_id']=='T10')['base_commit']
            self.assertNotEqual(base,assigned)
            self.assertEqual('UNDER_REVIEW',next(row for row in m.load(repo/'Docs/Production/WORKSTREAM_REGISTRY.json')['workstreams'] if row['task_id']=='T10')['status'])
            self.assertFalse(self.git(repo,'remote'))

    def test_actual_consumer_rehearsal_and_adversarial_closure_mutations(self):
        with tempfile.TemporaryDirectory(prefix='t10-synthetic-no-remote-') as temporary:
            target=Path(temporary);repo,base,candidate=self.prepare_repo(target)
            export_commit,reports,export_args=self.prepare_exports(target,repo,candidate)
            spec=dict(candidate=candidate,base=base,integration_head=export_args['integration_head'],export_commit=export_commit,approved_at='2026-09-18T00:00:00Z')
            inputs=dict(gates=dict(gates={f'G{i}':dict(status='PASS') for i in range(1,15)}),
                path_validation=dict(passed=True,candidate=candidate,base=base),tests=dict(passed=True,records=['DIAGNOSTIC ONLY']),
                progression=dict(passed=True,candidate_commit=candidate),
                defect_dispositions=dict(diagnostic_only=True,defects=[dict(id='fixture',status='VERIFIED_CLOSED')]))
            observation=dict(schema_version=1,passed=True,task_id='T10',source_sha=candidate,
                bundle_is_observation_not_authority=True,quality_thresholds_unchanged=True,environment_exact=True,environment_fingerprint='DIAGNOSTIC ONLY',
                telemetry=dict(source_sha=candidate,task_id='T10',terminal_class='SUCCESS',**{k:0 for k in ('queue_seconds','run_seconds','gate_durations','rerun_count','c0_cycles','proof_cache_hits','artifact_bytes','terminal_gate')}),
                task_state=dict(task_id='T10',candidate_commit=candidate,snapshot_is_derived_not_authority=True))
            observation['environment_provenance']={key:'DIAGNOSTIC ONLY' for key in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH')}
            inputs['factory_observation']=observation
            m.write(repo,m.EVIDENCE+'/CloseoutInputs/factory_observation.json',observation)
            m.assemble_records(repo,spec,inputs)
            # Complete chain reports all concrete boundaries even if broad historical
            # migration checks have unrelated fixture/environment prerequisites.
            snapshot=m.run_cli(repo,m.PRODUCTION+'/task_state_snapshot.py','T10','--candidate',candidate,'--last-gate','G1-G14','--output',m.TASK+'/task-state.json')
            m.successful(snapshot);reports.append(snapshot)
            completion=m.load(repo/m.TASK/'verified-completion.json')
            m.write_approval_retention(repo,spec,completion)
            for command in [
                ('evidence_retention.py','validate-manifest',m.EVIDENCE+'/APPROVAL_EVIDENCE_MANIFEST.json'),
                ('evidence_retention.py','validate-manifest',m.EVIDENCE+'/REVIEW_EVIDENCE_MANIFEST.json'),
                ('closure_validator.py',m.TASK+'/verified-completion.json'),
                ('validate_migration.py',),('architecture_v3.py','validate'),('architecture_v31.py','validate'),('validate_architecture_v32_t10.py',),
                ('validate_integration_scope.py','--base',base,'--head',candidate),
                ('factory_closeout_gate.py','--task','T10','--candidate',candidate,'--observation',m.EVIDENCE+'/CloseoutInputs/factory_observation.json')]:
                report=m.run_cli(repo,m.PRODUCTION+'/'+command[0],*command[1:]);reports.append(report)
            failures=[r for r in reports if r['exit_code']]
            import os
            if os.environ.get('T10_REHEARSAL_REPORT'):
                summary=dict(diagnostic_only=True, production_approval=False, no_remote=True, consumers=[dict(command=r['command'],exit_code=r['exit_code'],stdout_sha256=m.digest(r['stdout'].encode()), errors=json.loads(r['stdout']).get('errors',[])) for r in reports])
                Path(os.environ['T10_REHEARSAL_REPORT']).write_bytes(m.encoded(summary))
            self.assertFalse(failures,json.dumps([dict(command=r['command'], errors=json.loads(r['stdout']).get('errors'), stderr=r['stderr']) for r in failures],indent=2))
            # Negative tests exercise actual closure CLI and refresh retention hashes
            # so each assertion reaches the intended semantic boundary.
            for name,mutate,expected in [
                ('C7 supplement',lambda d:d['critics']['C7'].pop('deterministic_supplement'),'deterministic supplement'),
                ('independence',lambda d:d['critics']['C3'].update(independent_runtime=False),'independent runtime'),
                ('index identity',lambda d:d['evidence'].update(provenance_hash='0'*64),'index hash mismatch'),
                ('raw hash',lambda d:d['critics']['C2'].update(raw_record_sha256='0'*64),'raw critic record hash mismatch')]:
                with self.subTest(name=name):
                    value=copy.deepcopy(completion);mutate(value)
                    m.write(repo,m.TASK+'/verified-completion.json',value);m.write_approval_retention(repo,spec,value)
                    report=m.run_cli(repo,m.PRODUCTION+'/closure_validator.py',m.TASK+'/verified-completion.json')
                    self.assertNotEqual(report['exit_code'],0);self.assertIn(expected,report['stdout'])
            self.assertFalse(self.git(repo,'remote'))


if __name__=='__main__': unittest.main()
