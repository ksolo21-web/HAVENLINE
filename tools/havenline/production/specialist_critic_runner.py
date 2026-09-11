#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, io, json, math, os, pathlib, subprocess, time, urllib.request
from typing import Any
from lib import ROOT, DOCS, load_json, ensure_score_strictly_above_nine

SUPPORTED={"C3","C4","C5","C7","C8","C10","C11"}
HAVENLINE_CONTRACT="""Havenline's permanent gameplay language is MOVE -> AUTO-INTERACT -> GATHER -> VISIBLY CARRY -> DELIVER -> TRANSFORM -> RESCUE -> BUILD/UPGRADE -> EXPLORE -> DEFEND. Preserve one primary movement joystick, automatic collection/gather/attack/contextual unload/rescue, and minimal deliberate-choice controls. Do not drift into button-heavy RPG combat, 4X warfare, complicated manual inventory, energy walls, mandatory payment, hidden spend-based difficulty, fake discounts, or mandatory multiplayer. Difficulty/depth/scale may grow while control complexity stays simple. Level 100 is the launch cap. F2P completion must remain realistic."""

def digest(path:pathlib.Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def load_manifest(path:pathlib.Path,cid:str,candidate:str)->dict:
    d=json.loads(path.read_text());errors=[]
    if d.get('critic_id')!=cid:errors.append('critic mismatch')
    if d.get('candidate_commit')!=candidate:errors.append('candidate mismatch')
    if not d.get('groups'):errors.append('groups missing')
    execution=load_json(DOCS/'CRITIC_EXECUTION.json');categories=set()
    for group in d.get('groups',[]):
        if not group.get('id') or not group.get('items'):errors.append('invalid group')
        for item in group.get('items',[]):
            p=ROOT/item.get('path','');categories.add(item.get('category'))
            if not p.is_file():errors.append('missing '+item.get('path',''))
            elif digest(p)!=item.get('sha256'):errors.append('hash mismatch '+item.get('path',''))
    missing=set(execution['critics'][cid].get('required_categories',[]))-categories
    if missing:errors.append('missing required categories: '+','.join(sorted(missing)))
    if errors:raise SystemExit('\n'.join(errors))
    return d

def evidence_text(group:dict)->str:
    chunks=[]
    for item in group['items']:
        p=ROOT/item['path'];kind=item['kind'];desc=item['description']
        if kind=='json':
            try:text=json.dumps(json.loads(p.read_text()),sort_keys=True,indent=2)
            except Exception:text=p.read_text(errors='replace')
            chunks.append(f"[{item['category']}] {desc}\n{text[:14000]}")
        elif kind=='text':chunks.append(f"[{item['category']}] {desc}\n{p.read_text(errors='replace')[:14000]}")
    return '\n\n'.join(chunks)

def evidence_board(group:dict,out:pathlib.Path):
    from PIL import Image,ImageDraw
    image_items=[i for i in group['items'] if i['kind'] in ('image','motion_frame')]
    if not image_items:return None
    if len(image_items)>18:raise SystemExit(f"group {group['id']} has >18 visual items; split it for review coverage")
    tiles=[]
    for item in image_items:
        im=Image.open(ROOT/item['path']).convert('RGB');im.thumbnail((520,300),Image.Resampling.LANCZOS);tiles.append((item,im))
    cols=3;rows=(len(tiles)+cols-1)//cols;w=1620;h=rows*350+45
    board=Image.new('RGB',(w,h),(20,31,43));draw=ImageDraw.Draw(board)
    draw.text((12,10),f"GROUP {group['id']} — source-bound evidence",fill='white')
    for n,(item,im) in enumerate(tiles):
        c=n%cols;r=n//cols;x=c*540+(540-im.width)//2;y=45+r*350+35
        label=f"{item['category']}: {pathlib.Path(item['path']).name}"
        draw.text((c*540+8,45+r*350+8),label[:84],fill='white');board.paste(im,(x,y))
    path=out/(group['id']+'-board.jpg');board.save(path,quality=93);return path

def request_local(board,text,prompt,schema,out:pathlib.Path,label:str):
    content=[]
    if board:
        from PIL import Image
        im=Image.open(board).convert('RGB');im.thumbnail((1664,1664),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format='JPEG',quality=92)
        content.append({'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()}})
    content.append({'type':'text','text':prompt+'\n\nSOURCE-BOUND STRUCTURED EVIDENCE:\n'+(text or '(visual evidence only)')})
    body={'model':'havenline-specialist-local','messages':[{'role':'user','content':content}], 'max_tokens':900,'temperature':0.2,'top_p':0.9,'seed':20260911,'chat_template_kwargs':{'enable_thinking':False},'response_format':{'type':'json_object','schema':schema},'cache_prompt':False}
    (out/(label+'-request.json')).write_text(json.dumps(body,indent=2)[:250000])
    req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=1200) as resp:raw=json.load(resp)
    (out/(label+'-raw.json')).write_text(json.dumps(raw,indent=2));choice=raw['choices'][0]
    if choice.get('finish_reason')!='stop':raise RuntimeError('incomplete reviewer response')
    parsed=json.loads(choice['message']['content']);(out/(label+'-raw.txt')).write_text(choice['message']['content']);return parsed

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--critic',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    cid=a.critic.upper();candidate=a.candidate
    if cid not in SUPPORTED:raise SystemExit('unsupported specialist critic '+cid)
    if len(candidate)!=40:raise SystemExit('candidate must be exact 40-char commit')
    independent=os.environ.get('HAVENLINE_INDEPENDENT_REVIEW_JOB')=='1'
    if not independent:raise SystemExit('independent specialist critic must run in a separately declared review job')
    manifest_path=(ROOT/a.manifest).resolve();manifest=load_manifest(manifest_path,cid,candidate)
    matrix=load_json(DOCS/'CRITIC_MATRIX.json');execution=load_json(DOCS/'CRITIC_EXECUTION.json');spec=execution['critics'][cid];dimensions=spec['dimensions'];checks=matrix['critics'][cid]['checks']
    out=(ROOT/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    cache=pathlib.Path(os.path.expanduser(os.environ.get('HAVENLINE_SPECIALIST_CACHE',execution['local_independent_runtime']['cache_path'])))
    m=json.loads((cache/'manifest.json').read_text())
    runtime=execution['local_independent_runtime'];assert m['publisher']==runtime['provider'] and m['base_model']==runtime['base_model']
    for item in m['files']:
        if digest(cache/item['filename'])!=item['sha256']:raise SystemExit('critic runtime hash mismatch '+item['filename'])
    servers=list((cache/'runtime').rglob('llama-server'))
    if len(servers)!=1:raise SystemExit('exact llama-server runtime not found')
    server=servers[0];env=dict(os.environ);env['LD_LIBRARY_PATH']=str(server.parent)+':'+env.get('LD_LIBRARY_PATH','')
    log=(out/'runtime.log').open('w');cmd=[str(server),'-m',str(cache/m['model_file']),'--mmproj',str(cache/m['projector_file']),'--host','127.0.0.1','--port','8080','-c','12288','-t','4','-tb','4','-ngl','0','--no-mmproj-offload','--parallel','1','--jinja','--image-min-tokens','768','--image-max-tokens','2048']
    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    rows=[];fatal=None
    try:
        for _ in range(180):
            if proc.poll() is not None:raise RuntimeError('local reviewer runtime exited')
            try:
                if json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)).get('status')=='ok':break
            except Exception:pass
            time.sleep(2)
        else:raise RuntimeError('local reviewer runtime not ready')
        score_props={k:{'type':'number','minimum':0,'maximum':10} for k in dimensions}
        schema={'type':'object','properties':{'observations':{'type':'array','items':{'type':'string'},'minItems':2,'maxItems':5},'defects':{'type':'array','items':{'type':'string'},'maxItems':5},'coverage_complete':{'type':'boolean'},'confidence':{'type':'string','enum':['low','medium','high']},'scores':{'type':'object','properties':score_props,'required':dimensions,'additionalProperties':False}},'required':['observations','defects','coverage_complete','confidence','scores'],'additionalProperties':False}
        base=f"""You are the independent {matrix['critics'][cid]['name']} for Havenline. You are reviewing exact candidate {candidate}. {HAVENLINE_CONTRACT}\nYour mandatory review checks are: {json.dumps(checks)}. Review only the supplied evidence and task scope; do not invent absent defects or silently excuse visible ones. Every mandatory dimension is scored 0-10. The forward PASS threshold is strictly ABOVE 9.0 unrounded, not >=9.0, and no average can hide a weak dimension. If any score is <=9.0, cite a concrete actionable defect in defects. If no actionable defect exists, defects MUST be [] exactly. Return JSON only. Do not claim physical-device 4K/60 unless the evidence explicitly contains physical certification."""
        for group in manifest['groups']:
            board=evidence_board(group,out);text=evidence_text(group);review=request_local(board,text,base+f"\nEvidence group: {group['id']}. Judge the complete group and every mandatory dimension.",schema,out,group['id'])
            scores=review.get('scores',{});errors=ensure_score_strictly_above_nine(scores)
            if set(scores)!=set(dimensions):errors.append('dimension coverage mismatch')
            if review.get('defects'):errors.append('unresolved defects')
            if review.get('coverage_complete') is not True:errors.append('coverage incomplete')
            if review.get('confidence') not in ('medium','high'):errors.append('confidence insufficient')
            rows.append({'group':group['id'],'review':review,'passed':not errors,'errors':errors,'lowest_score':min(scores.values()) if scores else None})
    except Exception as exc:fatal=type(exc).__name__+': '+str(exc)
    finally:
        proc.terminate()
        try:proc.wait(timeout=10)
        except Exception:proc.kill()
        log.close()
    dim_scores={d:min((r['review']['scores'][d] for r in rows if d in r.get('review',{}).get('scores',{})),default=0) for d in dimensions}
    defects=[f"{r['group']}: {d}" for r in rows for d in r.get('review',{}).get('defects',[])]
    confidence_order={'low':0,'medium':1,'high':2};confidence=min((r.get('review',{}).get('confidence','low') for r in rows),key=lambda x:confidence_order.get(x,0),default='low')
    raw={'critic_id':cid,'candidate':candidate,'groups':rows,'fatal_error':fatal};raw_path=out/'raw-output.json';raw_path.write_text(json.dumps(raw,indent=2)+'\n')
    passed=fatal is None and len(rows)==len(manifest['groups']) and all(r['passed'] for r in rows)
    record={'critic_id':cid,'provider':m['publisher'],'model':m['base_model'],'model_revision_expected':runtime['model_revision'],'request_or_run_id':os.environ.get('GITHUB_RUN_ID','local')+'/'+os.environ.get('GITHUB_JOB','specialist'),'candidate_hash':candidate,'input_manifest_hash':digest(manifest_path),'raw_output_path':str(raw_path.relative_to(ROOT)),'raw_output_hash':digest(raw_path),'scores':dim_scores,'defects':defects,'coverage_complete':fatal is None and len(rows)==len(manifest['groups']) and all(r.get('review',{}).get('coverage_complete') is True for r in rows),'confidence':confidence,'independent_runtime':True,'groups':rows,'fatal_error':fatal,'passed':passed}
    (out/'critic-record.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2));raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
