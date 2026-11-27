#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, pathlib, re
from lib import ROOT, DOCS, load_json, sha256_file
from reference_acceptance import declared_reference_dimensions, load_json_strict, playback_errors, record_errors, strict_json_loads
from critic_profile import resolve_critic

SPECIALIST_CRITICS=frozenset({'C3','C4','C5','C7','C8','C10','C11'})
EXTERNAL_CRITICS=frozenset({'C1','C2','C5'})

def _bound_file(path, digest, label):
    errors=[]
    if not isinstance(path,str) or not path or not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):
        return None,[label+" needs an actual path and 64-hex SHA256"]
    file=ROOT/path
    if file.is_symlink() or not file.resolve().is_relative_to(ROOT.resolve()):errors.append(label+" path escapes repository or is a symlink")
    elif not file.is_file():errors.append(label+" file missing")
    elif sha256_file(file)!=digest:errors.append(label+" hash mismatch")
    return (file if not errors else None),errors


def _bound_json(path, digest, label):
    file,errors=_bound_file(path,digest,label)
    if file is None:return {},errors
    try:
        value=load_json_strict(file)
        if not isinstance(value,dict):raise ValueError("must be an object")
        return value,errors
    except (OSError,ValueError,TypeError) as exc:return {},errors+[label+" invalid JSON: "+str(exc)]


def source_manifest(record,critic_id,candidate,spec):
    manifest,errors=_bound_json(record.get('input_manifest_path'),record.get('input_manifest_hash'),'input manifest')
    if not manifest:return manifest,[],errors+['input manifest is missing or empty']
    if manifest.get('critic_id')!=critic_id or manifest.get('candidate_commit')!=candidate:errors.append('input manifest critic/candidate identity mismatch')
    if record.get('task_id') is not None and manifest.get('task_id')!=record.get('task_id'):errors.append('input manifest task identity mismatch')
    if record.get('complete_evidence_index_sha256') is not None and manifest.get('complete_evidence_index_sha256')!=record.get('complete_evidence_index_sha256'):
        errors.append('input manifest complete evidence index identity mismatch')
    try:reference_dimensions=declared_reference_dimensions(manifest,critic_id,spec['dimensions'])
    except ValueError as exc:errors.append(str(exc));reference_dimensions=[]
    groups=manifest.get('groups');categories=set();group_ids=[]
    if not isinstance(groups,list) or not groups:errors.append('input manifest evidence groups missing');groups=[]
    for group in groups:
        if not isinstance(group,dict):errors.append('invalid input evidence group');continue
        group_ids.append(group.get('id'))
        if not isinstance(group.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',group['id']):errors.append('input evidence group identity missing or unsafe')
        items=group.get('items')
        if not isinstance(items,list) or not items:errors.append('input evidence group items missing');continue
        for item in items:
            if not isinstance(item,dict):errors.append('invalid input evidence item');continue
            if isinstance(item.get('category'),str):categories.add(item['category'])
            file,failures=_bound_file(item.get('path'),item.get('sha256'),'input evidence item');errors+=failures
            if file is not None and item.get('kind')=='json':
                try:load_json_strict(file)
                except (OSError,ValueError) as exc:errors.append('input evidence JSON invalid: '+str(exc))
    if len(set(x for x in group_ids if isinstance(x,str)))!=len(group_ids):errors.append('input evidence group IDs must be unique')
    missing=set(spec.get('required_categories',[]))-categories
    if missing:errors.append('input manifest missing required categories: '+','.join(sorted(missing)))
    return manifest,reference_dimensions,errors


def _specialist_report_errors(raw,record,manifest,dimensions,reference_dimensions):
    errors=[];cid=record['critic_id']
    # This runner sends contact sheets and text, not a playable temporal stream.
    if cid=='C5':errors.append('static specialist output is interim-only; independent full-cycle playback evidence is required for final C5')
    rows=raw.get('groups');source_groups=manifest.get('groups',[])
    if not isinstance(rows,list) or not rows:return errors+['raw specialist review groups missing']
    if [r.get('group') for r in rows if isinstance(r,dict)]!=[g.get('id') for g in source_groups if isinstance(g,dict)]:errors.append('raw specialist group coverage differs from input manifest')
    reviews=[]
    for row in rows:
        if not isinstance(row,dict):errors.append('invalid raw specialist group');continue
        review=row.get('review',{})
        response,failures=_bound_json(row.get('response_path'),row.get('response_sha256'),'original reviewer response');errors+=failures
        request,failures=_bound_json(row.get('request_path'),row.get('request_sha256'),'original reviewer request');errors+=failures
        request_text=json.dumps(request,sort_keys=True)
        for key in ('candidate_hash','input_manifest_hash'):
            value=record.get(key)
            if not isinstance(value,str) or not value or value not in request_text:errors.append('original reviewer request lacks exact '+key)
        if response!=review:errors.append('raw group differs from original reviewer response')
        # Manifest constraints are passed separately; reviewer JSON cannot waive them.
        projected=dict(review) if isinstance(review,dict) else {}
        projected['reference_sensitive_dimensions']=reference_dimensions
        errors += record_errors(projected,dimensions,cid,require_binding=False,reference_dimensions=reference_dimensions)
        reviews.append(projected)
    if raw.get('fatal_error') is not None:errors.append('raw specialist runtime failed')
    valid_scores=all(isinstance(r.get('scores'),dict) and set(r['scores'])==set(dimensions) and
                     all(type(v) in (int,float) and 0<=v<=10 for v in r['scores'].values()) for r in reviews)
    if valid_scores and reviews:
        expected={dim:min(r['scores'][dim] for r in reviews) for dim in dimensions}
        if record.get('scores')!=expected:errors.append('scores are not the minimum of original reviewer group scores')
    else:errors.append('original reviewer scores cannot be projected')
    expected_defects=[str(row.get('group'))+': '+str(defect) for row in rows if isinstance(row,dict)
                      for defect in (row.get('review',{}).get('defects',[]) if isinstance(row.get('review',{}),dict) and isinstance(row.get('review',{}).get('defects',[]),list) else [])]
    if record.get('defects')!=expected_defects:errors.append('defects differ from original reviewer responses')
    expected_coverage=raw.get('fatal_error') is None and len(rows)==len(source_groups) and all(r.get('coverage_complete') is True for r in reviews)
    if record.get('coverage_complete') is not expected_coverage:errors.append('coverage differs from original reviewer responses')
    order={'low':0,'medium':1,'high':2}
    confidence=min((r.get('confidence','low') for r in reviews),key=lambda x:order.get(x,0),default='low')
    if record.get('confidence')!=confidence:errors.append('confidence differs from original reviewer responses')
    return errors


def _security_report_errors(raw,record,manifest):
    errors=[]
    try:
        item=manifest['groups'][0]['items'][0]
        canonical=DOCS/'SECURITY_ATTACK_MATRIX.json'
        canonical_bytes=canonical.read_bytes()
        canonical_hash=hashlib.sha256(canonical_bytes).hexdigest()
        canonical_matrix=strict_json_loads(canonical_bytes)
        if item.get('path')!=str(canonical.relative_to(ROOT)) or item.get('sha256')!=canonical_hash:
            return ['security review input is not the current canonical attack matrix']
        matrix,failures=_bound_json(item.get('path'),item.get('sha256'),'attack matrix');errors+=failures
        if matrix!=canonical_matrix:errors.append('decoded attack matrix differs from current canonical bytes')
        if raw.get('protocol')!=canonical_matrix.get('protocol'):errors.append('security protocol differs from current canonical attack matrix')
        # A manifest-selected document never defines the mandatory assertions.
        attacks=canonical_matrix['attacks'];rows=raw['results']
        if [r['attack_id'] for r in rows]!=[a['id'] for a in attacks]:errors.append('raw attack coverage mismatch')
        scores={};defects=[]
        for attack,row in zip(attacks,rows):
            log,failures=_bound_file(row.get('log'),row.get('log_sha256'),'attack log');errors+=failures
            parsed=None
            if log is not None:
                for line in reversed(log.read_text().splitlines()):
                    if line.lstrip().startswith('{'):
                        try:parsed=strict_json_loads(line)
                        except ValueError as exc:errors.append('attack log JSON invalid: '+str(exc))
                        break
            if parsed!=row.get('result'):errors.append('attack result differs from original log')
            failures=[];aid=attack['id']
            if not isinstance(parsed,dict):failures.append('no JSON result')
            else:
                if parsed.get('attack_id')!=aid or parsed.get('candidate_commit')!=record['candidate_hash']:failures.append('attack identity mismatch')
                if parsed.get('passed') is not True:failures.append('adapter marked attack failed')
                for assertion in attack['required_assertions']:
                    if parsed.get('assertions',{}).get(assertion) is not True:failures.append('failed assertion '+assertion)
                for key in ('before_state_hash','after_state_hash'):
                    if not parsed.get(key):failures.append('missing '+key)
            if row.get('returncode')!=0:failures.append('adapter failed')
            scores[aid]=0.0 if failures else 10.0
            if failures:errors.append('raw attack failed: '+aid)
        if record.get('scores')!=scores:errors.append('security scores differ from actual attack results')
        if record.get('coverage_complete') is not (len(rows)==len(attacks)):errors.append('security coverage differs from actual attack results')
        if record.get('defects')!=[] or any(score!=10 for score in scores.values()):errors.append('security defects remain')
    except (OSError,KeyError,TypeError,ValueError,IndexError) as exc:errors.append('invalid source-bound security report: '+str(exc))
    return errors


def source_report_errors(record,manifest,dimensions,reference_dimensions):
    raw,errors=_bound_json(record.get('raw_output_path'),record.get('raw_output_hash'),'raw output')
    if not raw:return errors+['raw reviewer report is missing or empty']
    for key in ('critic_id','task_id','candidate_hash','provider','model','request_or_run_id','input_manifest_path','input_manifest_hash','complete_evidence_index_sha256','reference_acceptance','reference_sensitive_dimensions','independent_runtime','passed','status','approval_allowed'):
        if raw.get(key)!=record.get(key):errors.append('raw/record identity mismatch: '+key)
    for key in ('scores','defects','coverage_complete','confidence'):
        if raw.get(key)!=record.get(key):errors.append('raw/record review mismatch: '+key)
    errors+=record_errors(raw,dimensions,record.get('critic_id'),reference_dimensions=reference_dimensions)
    if raw.get('format')=='havenline-specialist-report-v2' and record.get('critic_id') in SPECIALIST_CRITICS:
        errors+=_specialist_report_errors(raw,record,manifest,dimensions,reference_dimensions)
    elif raw.get('format')=='havenline-security-report-v2' and record.get('critic_id')=='C9':
        errors+=_security_report_errors(raw,record,manifest)
    elif raw.get('format')=='havenline-external-independent-review-v1' and record.get('critic_id') in EXTERNAL_CRITICS:
        errors+=external_review_errors(raw,record,manifest,dimensions,reference_dimensions)
    elif raw.get('format')=='havenline-performance-review-v1' and record.get('critic_id')=='C6':
        errors+=external_review_errors(raw,record,manifest,dimensions,reference_dimensions,_performance=True)
    else:errors.append('raw output has no supported source-bound forward report; legacy bytes are non-approving')
    return errors


def external_review_errors(raw,record,manifest,dimensions,reference_dimensions,*,_performance=False):
    """Agent-native independent model review, backed by its actual session export.

    No API-wire identifiers are invented. The session/task identity must be the
    identity that actually reviewed these immutable inputs and media.
    """
    from shipping_visual_gate import _image_size, _video_metadata
    errors=[];transport=raw.get('review_transport',{})
    if record.get('critic_id') not in ({'C6'} if _performance else EXTERNAL_CRITICS):
        return ['external independent transport is restricted to C1/C2/C5; deterministic and other critic lanes retain their own gates']
    transport_kind='performance_review_v1' if _performance else 'external_independent_review_v1'
    if not isinstance(transport,dict) or transport.get('kind')!=transport_kind:
        return ['external independent review transport kind missing']
    session,failures=_bound_json(transport.get('session_path'),transport.get('session_sha256'),'original independent review session');errors+=failures
    if not session:return errors+['original independent session is missing or empty']
    if session.get('transport_kind')!=transport_kind:errors.append('original independent session transport mismatch')
    identity=session.get('reviewer',{})
    if not isinstance(identity,dict):identity={};errors.append('actual independent reviewer identity missing')
    if identity.get('kind')!='agent_model':errors.append('C1/C2/C5 require an actual independent agent/model review; human owner signoff is supplemental')
    reviewer=identity.get('identity');builder=manifest.get('builder_identity')
    if not isinstance(builder,str) or not builder.strip():errors.append('frozen input builder identity missing')
    if not isinstance(reviewer,str) or not reviewer.strip() or reviewer==builder:errors.append('reviewer must be a distinct actual agent/model identity')
    if reviewer!=manifest.get('independent_reviewer_identity'):errors.append('independent reviewer differs from frozen input assignment')
    if identity.get('independent') is not True:errors.append('original session does not attest independent review')
    for key in ('provider','model','request_or_run_id'):
        if not isinstance(identity.get(key),str) or not identity[key].strip() or identity[key]!=record.get(key):errors.append('actual reviewer identity mismatch: '+key)
    review=session.get('review')
    if not isinstance(review,dict):return errors+['original independent session review missing']
    for key in ('task_id','critic_id','candidate_hash','input_manifest_hash','complete_evidence_index_sha256','reference_acceptance','reference_sensitive_dimensions','scores','defects','coverage_complete','confidence','passed','status','independent_runtime'):
        if review.get(key)!=record.get(key):errors.append('external session/record mismatch: '+key)
    errors+=record_errors(review,dimensions,record['critic_id'],reference_dimensions=reference_dimensions)
    items=[item for group in manifest.get('groups',[]) if isinstance(group,dict) for item in group.get('items',[]) if isinstance(item,dict)]
    if review.get('reviewed_evidence')!=items:errors.append('original session does not cover every frozen evidence item')
    if _performance:
        source_kind=session.get('source_kind')
        if source_kind not in ('agent_native','api_request_response'):errors.append('performance original source kind must be agent_native or api_request_response')
        if source_kind=='api_request_response':
            api=session.get('api_transport',{})
            if not isinstance(api,dict):api={}
            request,failures=_bound_json(api.get('request_path'),api.get('request_sha256'),'original performance API request');errors+=failures
            response,failures=_bound_json(api.get('response_path'),api.get('response_sha256'),'original performance API response');errors+=failures
            request_text=json.dumps(request,sort_keys=True)
            for key in ('candidate_hash','input_manifest_hash'):
                if not isinstance(record.get(key),str) or record[key] not in request_text:errors.append('performance API request lacks exact '+key)
            try:
                if 'choices' in response:response=strict_json_loads(response['choices'][0]['message']['content'])
            except (ValueError,KeyError,IndexError,TypeError) as exc:errors.append('original performance API response invalid: '+str(exc));response={}
            if not isinstance(response,dict):response={};errors.append('original performance API response must be an object')
            projected={**response,'reference_sensitive_dimensions':reference_dimensions}
            errors+=record_errors(projected,dimensions,'C6',require_binding=False,reference_dimensions=reference_dimensions)
            for key in ('scores','defects','coverage_complete','confidence'):
                if response.get(key)!=review.get(key):errors.append('performance session differs from original API '+key)
        supplement=record.get('measured_supplement')
        if not isinstance(supplement,dict):supplement={};errors.append('actual measured performance supplement missing')
        if raw.get('measured_supplement')!=supplement or review.get('measured_supplement')!=supplement:
            errors.append('performance supplement differs from original reviewer source')
        if not any(item.get('path')==supplement.get('path') and item.get('sha256')==supplement.get('sha256') and item.get('category')=='performance_measurement' for item in items):
            errors.append('performance supplement is absent from the frozen input evidence')
        performance_path,failures=_bound_file(supplement.get('path'),supplement.get('sha256'),'measured performance supplement');errors+=failures
        if performance_path is not None:
            check=c6(performance_path,record['candidate_hash'])
            if check.get('passed') is not True:errors.append('quantitative measured performance gate failed')
            errors += ['measured performance: '+message for message in check.get('errors',[])]
        return errors
    visuals=[item for item in items if item.get('kind') in ('image','video','motion_video')]
    if not visuals:errors.append('external visual review has no actual media')
    cameras=set();candidate_hashes=set()
    for item in visuals:
        path,failures=_bound_file(item.get('path'),item.get('sha256'),'external review media');errors+=failures
        if path is None:continue
        try:
            if item.get('kind')=='image':_image_size(path.read_bytes())
            else:_video_metadata(path.read_bytes())
        except Exception as exc:errors.append('external review media cannot be decoded: '+str(exc))
        if item.get('role')=='candidate':
            if record['critic_id'] in ('C1','C2') and item.get('sha256') in candidate_hashes:
                errors.append('duplicate candidate capture bytes cannot add independent camera-view coverage')
            candidate_hashes.add(item.get('sha256'))
            if isinstance(item.get('camera'),str) and item['camera'].strip():cameras.add(item['camera'])
    if record['critic_id'] in ('C1','C2') and (len(cameras)<2 or len(candidate_hashes)<2):
        errors.append('external visual review needs at least two distinct candidate capture bytes and camera views')
    if record['critic_id']=='C1' and not {'A','B'}<={item.get('reference_id') for item in visuals if item.get('role')=='reference'}:
        errors.append('C1 external review must include actual locked A and B reference pixels')
    if review.get('pixel_review_complete') is not True:errors.append('original independent session did not complete actual pixel review')
    if record['critic_id']=='C5':
        errors+=playback_errors(review,[item for item in visuals if item.get('kind') in ('video','motion_video')],root=ROOT)
    return errors


def ingest_performance_review(manifest_path,session_path,out,candidate):
    """Export actual original C6 judgment verbatim, then validate its measurements."""
    manifest_path=pathlib.Path(manifest_path).resolve();session_path=pathlib.Path(session_path).resolve();out=pathlib.Path(out).resolve()
    for path in (manifest_path,session_path,out):
        if not path.is_relative_to(ROOT.resolve()):raise ValueError('current review evidence must be retained within the repository')
    session=load_json_strict(session_path)
    if not isinstance(session,dict) or not isinstance(session.get('review'),dict) or not isinstance(session.get('reviewer'),dict):
        raise ValueError('actual original performance session/reviewer is missing')
    review=session['review'];identity=session['reviewer']
    if review.get('critic_id')!='C6' or review.get('candidate_hash')!=candidate:raise ValueError('original performance reviewer candidate/critic mismatch')
    if review.get('input_manifest_hash')!=sha256_file(manifest_path):raise ValueError('original review input manifest hash mismatch')
    out.mkdir(parents=True,exist_ok=True)
    raw_path=out/'performance-review-raw.json';record_path=out/'critic-record.json'
    if raw_path.exists() or record_path.exists():raise ValueError('refusing to overwrite retained performance review evidence')
    # Scores, binding and disposition come only from the original review. This
    # exporter never stamps a new policy or invents scores from passing metrics.
    record={**review,**{key:identity.get(key) for key in ('provider','model','request_or_run_id')},
            'input_manifest_path':str(manifest_path.relative_to(ROOT))}
    raw={**record,'format':'havenline-performance-review-v1','review_transport':{'kind':'performance_review_v1',
        'session_path':str(session_path.relative_to(ROOT)),'session_sha256':sha256_file(session_path)}}
    raw_path.write_text(json.dumps(raw,indent=2,allow_nan=False)+'\n')
    record.update(raw_output_path=str(raw_path.relative_to(ROOT)),raw_output_hash=sha256_file(raw_path))
    record_path.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
    result=validate_raw(record_path,'C6',candidate)
    result['record_path']=str(record_path.relative_to(ROOT))
    return result


def validate_raw(path:pathlib.Path,critic_id:str,candidate:str):
    cfg=load_json(DOCS/"CRITIC_MATRIX.json");execution=load_json(DOCS/"CRITIC_EXECUTION.json")
    if critic_id not in cfg["critics"]:raise SystemExit(f"unknown critic {critic_id}")
    try:d=load_json_strict(path)
    except (OSError,ValueError) as exc:return {'critic_id':critic_id,'candidate':candidate,'passed':False,'errors':['review record invalid JSON: '+str(exc)]}
    errors=[]
    if not isinstance(d,dict):
        return {"critic_id":critic_id,"candidate":candidate,"passed":False,"errors":["review record must be an object"],"record":d}
    for k in ("critic_id","provider","model","request_or_run_id","candidate_hash","input_manifest_hash","raw_output_path","raw_output_hash","scores","defects","coverage_complete","confidence"):
        if k not in d:errors.append("missing "+k)
    if d.get("critic_id")!=critic_id:errors.append("critic id mismatch")
    if d.get("candidate_hash")!=candidate:errors.append("candidate hash mismatch")
    for k in ("provider","model","request_or_run_id","input_manifest_hash","raw_output_path","raw_output_hash"):
        if not d.get(k):errors.append("empty "+k)
    try:
        spec,_=resolve_critic(d.get("task_id"),critic_id,execution,cfg)
    except ValueError as exc:
        errors.append(str(exc));spec=execution["critics"][critic_id]
    expected=set(spec.get("dimensions",[]))
    if expected and (not isinstance(d.get("scores"),dict) or set(d["scores"])!=expected):errors.append("mandatory dimension coverage mismatch")
    manifest,reference_dimensions,failures=source_manifest(d,critic_id,candidate,spec);errors+=failures
    errors+=record_errors(d,spec.get("dimensions",[]),critic_id,reference_dimensions=reference_dimensions)
    if d.get("defects")!=[]:errors.append("unresolved defects present")
    if d.get("coverage_complete") is not True:errors.append("coverage incomplete")
    if d.get("confidence") not in ("medium","high"):errors.append("confidence insufficient")
    if cfg["critics"][critic_id].get("independent_model_required") and d.get("independent_runtime") is not True:errors.append("required independent runtime not proven")
    errors+=source_report_errors(d,manifest,spec.get('dimensions',[]),reference_dimensions)
    if d.get("passed") is False:errors.append("critic record marked failed")
    return {"critic_id":critic_id,"candidate":candidate,"passed":not errors,"errors":errors,"record":d}

def c6(performance_path:pathlib.Path,candidate:str):
    budgets=load_json(DOCS/"PERFORMANCE_BUDGETS.json");errors=[]
    try:perf=load_json_strict(performance_path)
    except (OSError,ValueError) as exc:return {'critic_id':'C6','candidate':candidate,'passed':False,'errors':['performance evidence invalid JSON: '+str(exc)]}
    if not isinstance(perf,dict):return {'critic_id':'C6','candidate':candidate,'passed':False,'errors':['performance evidence must be an object']}
    if perf.get("candidate_commit")!=candidate:errors.append("candidate mismatch")
    soft=budgets["global_soft_budgets"]
    checks={"visible_triangles":soft["visible_triangles"],"draw_calls":soft["draw_calls"],"materials_visible":soft["materials_visible"],"texture_gpu_memory_mb":soft["texture_gpu_memory_mb"],"process_memory_mb":soft["process_memory_mb"],"physics_active_bodies":soft["physics_active_bodies"],"animated_rigs_active":soft["animated_rigs_active"],"npc_companion_active_population":soft["npc_companion_active_population"],"storage_download_mb":soft["storage_download_mb"]}
    for key,limit in checks.items():
        value=perf.get(key)
        if value is None:errors.append(f"missing metric {key}")
        elif type(value) not in (int,float) or value<0 or not value<=limit:errors.append(f"{key} must be finite, nonnegative and <= {limit}")
    for key,limit in (("cpu_frame_ms",soft["cpu_frame_ms"]),("gpu_frame_ms_where_measurable",soft["gpu_frame_ms_where_measurable"])):
        value=perf.get(key)
        if value is None and key=='cpu_frame_ms':errors.append('missing metric '+key)
        elif value is not None and (type(value) not in (int,float) or value<0 or not value<=limit):errors.append(f"{key} must be finite, nonnegative and <= {limit}")
    return {"critic_id":"C6","candidate":candidate,"passed":not errors,"errors":errors,"measurement":perf,"note":"Quantitative specialist gate; not T68/T69 certification."}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate-raw");v.add_argument("--critic",required=True);v.add_argument("--candidate",required=True);v.add_argument("--raw",required=True)
    p=sub.add_parser("performance");p.add_argument("--candidate",required=True);p.add_argument("--record",required=True)
    i=sub.add_parser('ingest-performance-review')
    for key in ('candidate','manifest','session','out'):i.add_argument('--'+key,required=True)
    a=ap.parse_args()
    if a.cmd=='validate-raw':result=validate_raw(pathlib.Path(a.raw),a.critic,a.candidate)
    elif a.cmd=='ingest-performance-review':result=ingest_performance_review(ROOT/a.manifest,ROOT/a.session,ROOT/a.out,a.candidate)
    else:result=c6(pathlib.Path(a.record),a.candidate)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result["passed"] else 1)
if __name__=="__main__":main()
