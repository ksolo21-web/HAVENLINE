#!/usr/bin/env python3
"""Diagnostic-only transport and real reviewer checks; never grants task approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_SHA = 'c7a18d002fe8d0f3978370f3e4567ba88bfe17e8'
RUN_ID = 35353927324
ARTIFACT_ID = 10551832949
ARCHIVE_SHA = 'd5b5c5d91b91f7db0ddde5b32a33e7cb7118f134e44907b21374d8ddf3fe7171'
ARCHIVE_SIZE = 23599433
BRANCH = 'refs/heads/havenline/T10-pipeline-canary'
CRITICS = ('C3', 'C4', 'C7')


def load(path): return json.loads(Path(path).read_text())
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def verify_archive(archive, artifact, run):
    assert run['id'] == RUN_ID and run['head_sha'] == EVIDENCE_SHA and run['status'] == 'completed', 'evidence run identity mismatch'
    assert run.get('conclusion') == 'failure', 'historical run conclusion mismatch'
    assert artifact['id'] == ARTIFACT_ID and artifact['name'] == 'havenline-task10-critic-input-' + EVIDENCE_SHA, 'evidence artifact identity mismatch'
    assert artifact['workflow_run']['id'] == RUN_ID and artifact['workflow_run']['head_sha'] == EVIDENCE_SHA, 'artifact run binding mismatch'
    assert artifact.get('expired') is False, 'artifact expired'
    assert artifact['size_in_bytes'] == ARCHIVE_SIZE == Path(archive).stat().st_size, 'archive size mismatch'
    assert artifact['digest'] == 'sha256:' + ARCHIVE_SHA and digest(archive) == ARCHIVE_SHA, 'archive digest mismatch'


def safe_extract(archive, target):
    target = Path(target)
    assert not target.exists(), 'extraction target must not exist'
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist(); seen = set(); total = 0
        for info in infos:
            name = info.filename; parts = PurePosixPath(name).parts
            assert name and '\\' not in name and not name.startswith('/') and '..' not in parts and ':' not in name, 'unsafe archive path'
            normalized = PurePosixPath(name).as_posix().rstrip('/')
            assert normalized not in seen, 'duplicate archive entry'
            seen.add(normalized)
            assert not stat.S_ISLNK(info.external_attr >> 16), 'archive symlink'
            assert not info.flag_bits & 1, 'encrypted archive entry'
            total += info.file_size
            assert total <= 512 * 1024 * 1024 and len(infos) <= 10000, 'archive expansion bound exceeded'
        target.mkdir(parents=True)
        z.extractall(target)


def verify_package(root):
    root = Path(root); index = load(root/'evidence-index.json')
    assert index['candidate'] == EVIDENCE_SHA and index['files'], 'index identity mismatch'
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    assert actual == set(index['files']) | {'evidence-index.json'}, 'index coverage mismatch'
    for rel, expected in index['files'].items():
        assert digest(root/rel) == expected, 'indexed digest mismatch: ' + rel
    for cid in CRITICS:
        manifest = load(root/(cid+'-manifest.json'))
        assert manifest['candidate_commit'] == EVIDENCE_SHA and manifest['critic_id'] == cid, 'manifest identity mismatch'


def verify_responses(manifest, folder):
    """Inspect actual completion envelopes; never infer completion from summaries."""
    folder = Path(folder); cid = manifest['critic_id']; rows = []
    for group in manifest['groups']:
        name = group['id']
        assert re.fullmatch(r'[A-Za-z0-9_-]+', name), 'unsafe group id'
        envelope = load(folder/(name+'-raw.json')); choice = envelope['choices'][0]
        assert choice.get('finish_reason') == 'stop', 'incomplete response: ' + name
        review = json.loads(choice['message']['content'])
        usage = envelope.get('usage', {})
        tokens = usage.get('completion_tokens')
        assert type(tokens) is int and 0 < tokens <= 900, 'completion token bound: ' + name
        if cid in CRITICS:
            observations = review.get('observations')
            assert isinstance(observations, list) and len(observations) == 2 and all(isinstance(x,str) and len(x)<=160 for x in observations), 'observation bound: ' + name
            defects = review.get('defects')
            assert isinstance(defects,list) and len(defects)<=5 and all(isinstance(x,str) and len(x)<=160 for x in defects), 'defect bound: ' + name
        rows.append(dict(group=name,finish_reason='stop',completion_tokens=tokens))
    return rows


def verify_runtime(record, execution, lock):
    runtime=execution['local_independent_runtime']
    assert runtime['provider']==lock['publisher'] and runtime['base_model']==lock['base_model'] and runtime['model_revision']==lock['revision'], 'runtime configuration/lock mismatch'
    expected=dict(provider=runtime['provider'],model=runtime['base_model'],model_revision_actual=runtime['model_revision'],model_revision_expected=runtime['model_revision'],runtime_release=lock['runtime_release'])
    for key,value in expected.items():
        assert value and record.get(key)==value, 'review runtime mismatch: '+key


def verify_requests(manifest, folder, dimensions):
    folder=Path(folder)
    expected_names={group['id']+'-request.json' for group in manifest['groups']}
    assert {p.name for p in folder.glob('*-request.json')}==expected_names, 'request coverage mismatch'
    scores=dict(type='object',properties={d:dict(type='number',minimum=0,maximum=10) for d in dimensions},required=dimensions,additionalProperties=False)
    for name in sorted(expected_names):
        request=load(folder/name)
        for key,value in dict(max_tokens=900,temperature=0.2,top_p=0.9,seed=20260911).items():
            assert type(request.get(key)) is type(value) and request[key]==value, 'request setting mismatch: '+name+': '+key
        assert request.get('chat_template_kwargs')=={'enable_thinking':False} and request['chat_template_kwargs']['enable_thinking'] is False, 'thinking enabled: '+name
        assert request.get('cache_prompt') is False, 'prompt caching enabled: '+name
        response=request.get('response_format',{})
        assert response.get('type')=='json_object', 'response format mismatch: '+name
        schema=response.get('schema',{})
        assert schema.get('properties',{}).get('scores')==scores, 'score schema mismatch: '+name
        assert 'scores' in schema.get('required',[]), 'scores not required: '+name
        for field in ('observations','defects'):
            prop=schema['properties'][field]
            assert prop.get('items')=={'type':'string','maxLength':160}, 'string schema bound mismatch: '+name
        assert schema['properties']['observations'].get('minItems')==2 and schema['properties']['observations'].get('maxItems')==2 and schema['properties']['defects'].get('maxItems')==5, 'array schema bound mismatch: '+name


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare');p.add_argument('--archive',required=True);p.add_argument('--artifact',required=True);p.add_argument('--run',required=True);p.add_argument('--target',default='critic-input')
    p=sub.add_parser('finish');p.add_argument('--critic',choices=CRITICS,required=True);p.add_argument('--folder',default='specialist-review')
    ap.add_argument('--tool-sha',required=True);ap.add_argument('--report',required=True)
    a=ap.parse_args();result=dict(diagnostic_only=True,task_approved=False,reusable_for_approval=False,tool_sha=a.tool_sha,evidence_sha=EVIDENCE_SHA,evidence_run_id=RUN_ID,evidence_artifact_id=ARTIFACT_ID,evidence_archive_sha256=ARCHIVE_SHA,passed=False,transport_passed=False,critic_result=None,errors=[])
    try:
        assert os.environ.get('GITHUB_REF') == BRANCH, 'dedicated canary branch required'
        assert re.fullmatch('[0-9a-f]{40}',a.tool_sha) and a.tool_sha==os.environ.get('GITHUB_SHA'), 'tool source identity mismatch'
        if a.mode=='prepare':
            verify_archive(a.archive,load(a.artifact),load(a.run));safe_extract(a.archive,ROOT/a.target);verify_package(ROOT/a.target)
            from build_critic_evidence import prompt_errors
            for cid in CRITICS:
                manifest=load(ROOT/a.target/(cid+'-manifest.json'))
                errors=prompt_errors(manifest)
                assert not errors, str(errors)
        else:
            sys.path.insert(0,str(ROOT/'tools/havenline/production'))
            from critic_harness import validate_raw
            from critic_profile import resolve_critic
            from specialist_evidence_manifest import validate
            from aggregate_critics import verify_original
            from build_critic_evidence import prompt_errors
            manifest_path=ROOT/'critic-input'/(a.critic+'-manifest.json');manifest=load(manifest_path)
            errors=validate(manifest)+prompt_errors(manifest)
            assert not errors, str(errors)
            folder=ROOT/a.folder;record=load(folder/'critic-record.json');raw=load(folder/'raw-output.json')
            execution=load(ROOT/'Docs/Production/CRITIC_EXECUTION.json')
            verify_runtime(record,execution,load(ROOT/'tools/havenline/production/critic_runtime_lock.json'))
            spec,_=resolve_critic('T10',a.critic,execution,load(ROOT/'Docs/Production/CRITIC_MATRIX.json'))
            assert record['input_manifest_hash']==digest(manifest_path), 'reviewed manifest mismatch'
            result['critic_id']=a.critic
            # Preserve a genuine product failure independently of transport diagnostics.
            # Neither a complete response nor a transport pass grants product approval.
            gate=validate_raw(folder/'critic-record.json',a.critic,EVIDENCE_SHA)
            result['critic_result']=gate
            result['original_validation_errors']=[]
            try:
                verify_original(record,raw,manifest,a.critic,EVIDENCE_SHA)
            except Exception as exc:
                result['original_validation_errors'].append(type(exc).__name__+': '+str(exc))
            result['groups']=verify_responses(manifest,folder)
            verify_requests(manifest,folder,spec['dimensions'])
            result['transport_passed']=True
            assert gate['passed'], str(gate['errors'])
            assert not result['original_validation_errors'], str(result['original_validation_errors'])
        result['passed']=True
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    write(a.report,result)
    print(json.dumps(result));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
