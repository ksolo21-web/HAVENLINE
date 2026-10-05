#!/usr/bin/env python3
"""Preserve original reviews and export canonical records without assigning scores.

Two stages avoid a self-referential export commit. This tool never approves a task.
API metadata, downloaded archives, reviews and an existing integration SHA are inputs.
"""
import argparse
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/havenline/production'))
from critic_harness import validate_raw, c6
from closure_validator import RAW_ACCEPTANCE_RULE, validate_raw_critic_record
from evidence_retention import validate_manifest
from aggregate_critics import verify_original, verify_performance_binding

CRITICS = ('C1', 'C2', 'C3', 'C4', 'C6', 'C7')
EXPORT = 'Docs/Production/T10/ReviewExports'
RAW = 'Docs/Production/T10/CriticRaw'
EVIDENCE = 'Docs/Production/Evidence/T10'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def encoded(value): return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)


def verify_archive(archive, artifact, run, candidate, retained=False):
    assert run.get('head_sha') == candidate and run.get('status') == 'completed' and run.get('conclusion') == 'success', 'successful exact-source run required'
    assert type(run.get('id')) is int and type(artifact.get('id')) is int, 'numeric API identity required'
    assert artifact.get('workflow_run', {}).get('id') == run['id'] and artifact['workflow_run'].get('head_sha') == candidate, 'artifact run/source mismatch'
    assert artifact.get('expired') is False and artifact.get('size_in_bytes') == Path(archive).stat().st_size, 'artifact size/expiry mismatch'
    assert artifact.get('digest') == 'sha256:' + sha(archive), 'artifact digest mismatch'
    if retained:
        assert artifact.get('name') == 'havenline-task10-critic-input-' + candidate, 'review artifact name mismatch'
        created = datetime.fromisoformat(artifact['created_at'].replace('Z', '+00:00'))
        expires = datetime.fromisoformat(artifact['expires_at'].replace('Z', '+00:00'))
        # API retention is day-based; a small upload-duration offset is possible.
        assert 89.5*86400 <= (expires-created).total_seconds() <= 90.5*86400, '90-day artifact retention required'
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert len(names) == len(set(names)), 'duplicate archive entry'
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names), 'unsafe archive path'
        return {n: z.read(n) for n in names if not n.endswith('/')}


def verify_index(payload, candidate):
    index = json.loads(payload['evidence-index.json'])
    assert index['candidate'] == candidate and index['files'], 'index source or empty index'
    for name, digest in index['files'].items():
        assert name in payload and hashlib.sha256(payload[name]).hexdigest() == digest, 'indexed payload mismatch: ' + name
    allowed = set(index['files']) | {'evidence-index.json'}
    assert set(payload) == allowed, 'unaccounted retained payload'
    return index


def original_bundle(folder, manifest=None, actions_archive=None):
    target=io.BytesIO()
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        extras={}
        if manifest is not None:extras['input-manifest.json']=manifest
        if actions_archive is not None:extras['actions-artifact.zip']=actions_archive
        for name,contents in extras.items():
            assert not (folder/name).exists(), 'reserved bundle filename collision'
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,contents)
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                assert not path.is_symlink(), 'symlink in original evidence'
                info=zipfile.ZipInfo(path.relative_to(folder).as_posix(),(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,path.read_bytes())
    return target.getvalue()


def verify_reviews(records, payload, candidate, run_id=None):
    assert {p.name for p in records.iterdir() if p.is_dir()} == set(CRITICS), 'exact six critic directories required'
    originals = {}
    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        for cid in CRITICS:
            record_path = records/cid/'critic-record.json'
            record = load(record_path)
            if cid in ('C3','C4','C7'):
                runtime=load(ROOT/'Docs/Production/CRITIC_EXECUTION.json')['local_independent_runtime']
                assert record['provider']==runtime['provider'] and record['model']==runtime['base_model'], 'pinned reviewer provider/model mismatch'
                assert record['model_revision_actual']==record['model_revision_expected']==runtime['model_revision'], 'pinned reviewer revision mismatch'
                assert run_id is not None and str(record['request_or_run_id']).startswith(str(run_id)+'/'), 'review request run mismatch'
            raw_path = records/cid/Path(record['raw_output_path']).name
            raw_bytes = raw_path.read_bytes()
            assert hashlib.sha256(raw_bytes).hexdigest() == record['raw_output_hash'], 'original raw hash mismatch'
            manifest_bytes = payload[cid+'-manifest.json']
            assert hashlib.sha256(manifest_bytes).hexdigest() == record['input_manifest_hash'], 'reviewed input hash mismatch'
            verify_original(record, json.loads(raw_bytes), json.loads(manifest_bytes), cid, candidate)
            normalized = dict(record, raw_output_path=str(raw_path.resolve()))
            normalized_path = temp/(cid+'.json');normalized_path.write_bytes(encoded(normalized))
            result = validate_raw(normalized_path, cid, candidate)
            assert result['passed'], result['errors']
            originals[cid] = (record_path.read_bytes(), raw_bytes, record)
        performance = temp/'performance.json';performance.write_bytes(payload['performance.json'])
        verify_performance_binding(performance, json.loads(payload['C6-manifest.json']), candidate)
        result = c6(performance, candidate)
        assert result['passed'], result['errors']
    return originals


def verify_hosted_artifacts(metadata, records, run, candidate):
    assert set(metadata)=={'C3','C4','C7'}, 'exact hosted critic artifacts required'
    verified={}
    for cid,row in metadata.items():
        artifact=row['artifact'];archive=Path(row['archive'])
        assert artifact.get('name')==f'havenline-task10-{cid}-{candidate}', 'hosted critic artifact name mismatch'
        payload=verify_archive(archive,artifact,run,candidate)
        normalized={}
        for name,contents in payload.items():
            rel=name.removeprefix('specialist-review/')
            assert rel not in normalized, 'normalized artifact path collision'
            normalized[rel]=contents
        actual={p.relative_to(records/cid).as_posix():p.read_bytes() for p in (records/cid).rglob('*') if p.is_file()}
        assert actual==normalized, 'consumed review differs from immutable Actions artifact'
        verified[cid]=dict(artifact=artifact,archive_bytes=archive.read_bytes())
    return verified


def canonical_index(payload, candidate):
    original=verify_index(payload,candidate)
    return encoded(dict(schema_version=1,task_id='T10',candidate_commit=candidate,file_count=len(original['files']),files=original['files'],source_evidence_index_sha256=hashlib.sha256(payload['evidence-index.json']).hexdigest()))


def verify_export_lineage(candidate, integration_head, export_commit):
    for commit in (candidate,integration_head,export_commit):
        assert re.fullmatch('[0-9a-f]{40}',commit), 'exact source lineage required'
    for ancestor,descendant in ((candidate,integration_head),(integration_head,export_commit)):
        subprocess.run(['git','merge-base','--is-ancestor',ancestor,descendant],cwd=ROOT,check=True)


def canonical(cid, original, candidate, run, artifact, index_hash, export_commit):
    record_bytes, raw_bytes, record = original
    links = dict(original_record_path=f'{EXPORT}/{cid}-original-record.json', original_record_sha256=hashlib.sha256(record_bytes).hexdigest(), original_raw_output_path=f'{EXPORT}/{cid}-original-raw-output.json', original_raw_output_sha256=hashlib.sha256(raw_bytes).hexdigest(), original_input_manifest_sha256=record['input_manifest_hash'])
    result = dict(task_id='T10', critic_id=cid, candidate_commit=candidate, workflow_run_id=run['id'], artifact_id=artifact['id'], artifact_sha256=artifact['digest'].removeprefix('sha256:'), complete_evidence_index_sha256=index_hash, input_manifest_sha256=index_hash, status='PASS', passed=True, coverage_complete=record['coverage_complete'], defects=record['defects'], scores=record['scores'], confidence=record['confidence'], score_reuse=False, minimum_dimension_score=min(record['scores'].values()), review_export_commit=export_commit, acceptance_rule=RAW_ACCEPTANCE_RULE, **{k:record[k] for k in ('provider','model','request_or_run_id')}, **links)
    errors=validate_raw_critic_record(result,cid,'T10',candidate,run['id'],artifact['id'],result['artifact_sha256'],index_hash,record['scores'],export_commit)
    assert not errors, errors
    return result


def export(args):
    candidate=args.candidate
    assert re.fullmatch('[0-9a-f]{40}',candidate), 'exact candidate required'
    assert re.fullmatch('[0-9a-f]{40}',args.integration_head), 'exact integration head required'
    subprocess.run(['git','merge-base','--is-ancestor',candidate,args.integration_head],cwd=ROOT,check=True)
    run=load(args.run);artifact=load(args.artifact)
    regression_run=load(args.regression_run);regression_artifact=load(args.regression_artifact)
    payload=verify_archive(args.archive,artifact,run,candidate,True)
    assert regression_artifact.get('name')=='havenline-task10-first-milestone-'+candidate, 'regression artifact name mismatch'
    verify_archive(args.regression_archive,regression_artifact,regression_run,candidate)
    index=verify_index(payload,candidate)
    hosted=verify_hosted_artifacts(load(args.hosted_artifacts),Path(args.records_root).resolve(),run,candidate)
    originals=verify_reviews(Path(args.records_root).resolve(),payload,candidate,run['id'])
    files={}
    for cid,(record_bytes,raw_bytes,_) in originals.items():
        files[f'{EXPORT}/{cid}-original-record.json']=record_bytes
        files[f'{EXPORT}/{cid}-original-raw-output.json']=raw_bytes
        files[f'{EXPORT}/{cid}-original-bundle.zip']=original_bundle(Path(args.records_root)/cid,payload[cid+'-manifest.json'],hosted[cid]['archive_bytes'] if cid in hosted else None)
    files[f'{EXPORT}/regression-evidence.zip']=Path(args.regression_archive).read_bytes()
    files[f'{EXPORT}/regression-provenance.json']=encoded(dict(candidate_commit=candidate,integration_head=args.integration_head,run=run,artifact=artifact,regression_run=regression_run,regression_artifact=regression_artifact,hosted_critic_artifacts={cid:row['artifact'] for cid,row in hosted.items()}))
    if args.export_commit:
        assert re.fullmatch('[0-9a-f]{40}',args.export_commit), 'real original-export commit required'
        verify_export_lineage(candidate,args.integration_head,args.export_commit)
        for name,contents in files.items():
            assert git('show',args.export_commit+':'+name)==contents, 'export commit bytes differ: '+name
        index_bytes=canonical_index(payload,candidate)
        index_hash=hashlib.sha256(index_bytes).hexdigest()
        for cid in CRITICS:
            row=canonical(cid,originals[cid],candidate,run,artifact,index_hash,args.export_commit)
            row['original_bundle_path']=f'{EXPORT}/{cid}-original-bundle.zip'
            row['original_bundle_sha256']=hashlib.sha256(files[row['original_bundle_path']]).hexdigest()
            if cid in hosted:
                row['original_actions_artifact']=hosted[cid]['artifact']
                row['original_actions_archive_bundle_entry']='actions-artifact.zip'
            row['original_input_manifest_bundle_entry']='input-manifest.json'
            files[f'{RAW}/{cid}.json']=encoded(row)
        files[f'{EVIDENCE}/complete-evidence-index.json']=index_bytes
        manifest=dict(schema_version=1,task_id='T10',accepted_source=candidate,retention_class='review_evidence',records=[dict(kind='exact_review_evidence',sha256=artifact['digest'].removeprefix('sha256:'),locator=f"github-actions://ksolo21-web/HAVENLINE/runs/{run['id']}/artifacts/{artifact['id']}",reproducible=True,retention_days=90,created_at=artifact['created_at'],expires_at=artifact['expires_at'],artifact_name=artifact['name'],size_bytes=artifact['size_in_bytes'],content_identity=dict(original_run_id=run['id'],original_artifact_id=artifact['id'],original_artifact_sha256=artifact['digest'].removeprefix('sha256:'),complete_evidence_index_sha256=index_hash,indexed_files_verified=len(index['files'])))],regeneration_contract=dict(workflow='.github/workflows/havenline-task10-isolated.yml',exact_source=candidate,source_run_id=run['id'],source_artifact_id=artifact['id'],review_export_commit=args.export_commit,rule='Regeneration never substitutes for fresh independent review.'))
        checked=validate_manifest(manifest);assert checked['passed'],checked['errors']
        files[f'{EVIDENCE}/REVIEW_EVIDENCE_MANIFEST.json']=encoded(manifest)
    # Validate every input before any output; never overwrite conflicting evidence.
    out=Path(args.out)
    for name,contents in files.items():
        target=out/name
        assert not target.exists() or target.read_bytes()==contents, 'conflicting existing export '+name
    for name,contents in files.items():
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(contents)
    return dict(passed=True,candidate_commit=candidate,files=len(files),task_approved=False)


def main():
    ap=argparse.ArgumentParser()
    for key in ('candidate','integration-head','run','artifact','archive','regression-run','regression-artifact','regression-archive','records-root','hosted-artifacts','out'):ap.add_argument('--'+key,required=True)
    ap.add_argument('--export-commit')
    print(json.dumps(export(ap.parse_args())))
if __name__=='__main__':main()
