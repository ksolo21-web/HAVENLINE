#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, sys, time, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[3]
PROD=ROOT/'tools'/'havenline'/'production'
sys.path.insert(0,str(PROD))
from lib import DOCS, load_json, ensure_score_strictly_above_nine
from critic_profile import resolve_critic
import specialist_critic_runner as shared

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--candidate',required=True)
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    candidate=a.candidate
    if len(candidate)!=40: raise SystemExit('candidate must be exact 40-char commit')
    if os.environ.get('HAVENLINE_INDEPENDENT_REVIEW_JOB')!='1':
        raise SystemExit('C2 must run in a separately declared independent review job')

    manifest_path=(ROOT/a.manifest).resolve()
    manifest=shared.load_manifest(manifest_path,'C2',candidate)
    matrix=load_json(DOCS/'CRITIC_MATRIX.json')
    execution=load_json(DOCS/'CRITIC_EXECUTION.json')
    spec,checks=resolve_critic('T11','C2',execution,matrix)
    dimensions=spec['dimensions']
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)

    cache=pathlib.Path(os.path.expanduser(execution['local_independent_runtime']['cache_path']))
    runtime=execution['local_independent_runtime'];m=json.loads((cache/'manifest.json').read_text())
    if m.get('publisher')!=runtime['provider'] or m.get('base_model')!=runtime['base_model'] or m.get('revision')!=runtime['model_revision']:
        raise SystemExit('critic runtime identity mismatch')
    for item in m['files']:
        if shared.digest(cache/item['filename'])!=item['sha256']:
            raise SystemExit('critic runtime hash mismatch '+item['filename'])
    servers=list((cache/'runtime').rglob('llama-server'))
    if len(servers)!=1: raise SystemExit('exact llama-server runtime not found')
    server=servers[0];env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
    log=(out/'runtime.log').open('w')
    cmd=[str(server),'-m',str(cache/m['model_file']),'--mmproj',str(cache/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','12288','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','768','--image-max-tokens','2048']
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    rows=[];fatal=None
    try:
        for _ in range(180):
            if proc.poll() is not None: raise RuntimeError('local reviewer runtime exited')
            try:
                if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok': break
            except Exception: pass
            time.sleep(2)
        else: raise RuntimeError('local reviewer runtime not ready')

        schema=shared.response_schema('T11',dimensions)
        base=f"""You are the independent {matrix['critics']['C2']['name']} for Havenline candidate {candidate}. Review only the supplied source-bound rendered evidence. Mandatory checks: {json.dumps(checks)}. Inspect actual authored construction geometry, floor/structure contact, clipping, seams, intentional gaps, preview transparency, committing-state integrity, and cross-view consistency. Do not invent defects and do not excuse visible ones. Every mandatory dimension is scored 0-10. PASS requires every unrounded score strictly above 9.0, zero actionable defects, complete coverage, and at least medium confidence. Native 4K frames are software-rendered evidence, not physical-device certification. Return JSON only."""
        for group in manifest['groups']:
            board=shared.evidence_board(group,out)
            text=shared.evidence_text(group)
            review=shared.request_local(board,text,base+f"\nEvidence group: {group['id']}. Judge all mandatory C2 dimensions.",schema,out,group['id'])
            scores=review.get('scores',{})
            errors=ensure_score_strictly_above_nine(scores)
            if set(scores)!=set(dimensions): errors.append('dimension coverage mismatch')
            if review.get('defects'): errors.append('unresolved defects')
            if review.get('coverage_complete') is not True: errors.append('coverage incomplete')
            if review.get('confidence') not in ('medium','high'): errors.append('confidence insufficient')
            rows.append({'group':group['id'],'review':review,'passed':not errors,'errors':errors,'lowest_score':min(scores.values()) if scores else None})
    except Exception as exc:
        fatal=type(exc).__name__+': '+str(exc)
    finally:
        proc.terminate()
        try: proc.wait(timeout=10)
        except Exception: proc.kill()
        log.close()

    dim_scores={d:min((r['review']['scores'][d] for r in rows if d in r.get('review',{}).get('scores',{})),default=0) for d in dimensions}
    defects=[f"{r['group']}: {d}" for r in rows for d in r.get('review',{}).get('defects',[])]
    confidence_order={'low':0,'medium':1,'high':2}
    confidence=min((r.get('review',{}).get('confidence','low') for r in rows),key=lambda x:confidence_order.get(x,0),default='low')
    raw={'critic_id':'C2','task_id':'T11','candidate':candidate,'groups':rows,'fatal_error':fatal}
    raw_path=out/'raw-output.json';raw_path.write_text(json.dumps(raw,indent=2)+'\n')
    passed=fatal is None and len(rows)==len(manifest['groups']) and all(r['passed'] for r in rows)
    record={
        'task_id':'T11','critic_id':'C2','provider':m['publisher'],'model':m['base_model'],
        'model_revision_expected':runtime['model_revision'],'model_revision_actual':m['revision'],
        'runtime_release':m.get('runtime_release'),
        'request_or_run_id':os.environ.get('GITHUB_RUN_ID','local')+'/'+os.environ.get('GITHUB_JOB','C2'),
        'candidate_hash':candidate,'input_manifest_hash':shared.digest(manifest_path),
        'raw_output_path':str(raw_path.relative_to(ROOT)),'raw_output_hash':shared.digest(raw_path),
        'scores':dim_scores,'defects':defects,
        'coverage_complete':fatal is None and len(rows)==len(manifest['groups']) and all(r.get('review',{}).get('coverage_complete') is True for r in rows),
        'confidence':confidence,'independent_runtime':True,'groups':rows,'fatal_error':fatal,'passed':passed
    }
    (out/'critic-record.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))
    raise SystemExit(0 if passed else 1)

if __name__=='__main__':
    main()
