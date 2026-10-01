#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
HEX64=re.compile(r'^[0-9a-f]{64}$');HEX40=re.compile(r'^[0-9a-f]{40}$')
def load(name): return json.loads((DOCS/name).read_text())
def fail(errors,msg): errors.append(msg)

def progression(row,cfg):
    errors=[];nodes=row.get('nodes',[]);by={n.get('id'):n for n in nodes if n.get('id')}
    if len(by)!=len(nodes): fail(errors,'duplicate/missing progression node id')
    starts=[n for n in nodes if n.get('level')==1]
    if len(starts)!=1: fail(errors,'exactly one level-1 node required')
    level100=[n for n in nodes if n.get('level')==100]
    if not level100: fail(errors,'level 100 missing')
    for n in nodes:
        if n.get('purchase_required'): fail(errors,'purchase-required progression node '+str(n.get('id')))
        for c in n.get('costs',[]):
            if int(c.get('quantity',0))<=0: fail(errors,'nonpositive cost '+str(n.get('id')))
        for p in n.get('prerequisites',[]):
            if p not in by: fail(errors,'missing prerequisite '+str(p))
            elif by[p].get('level',0)>n.get('level',0): fail(errors,'nonmonotonic prerequisite '+str(n.get('id')))
    reachable=set()
    if starts:
        reachable.add(starts[0]['id'])
        changed=True
        while changed:
            changed=False
            for n in nodes:
                if n['id'] in reachable: continue
                if all(p in reachable for p in n.get('prerequisites',[])):
                    reachable.add(n['id']);changed=True
    missing=sorted(set(by)-reachable)
    if missing: fail(errors,'unreachable progression nodes: '+','.join(missing[:10]))
    if level100 and not any(n['id'] in reachable for n in level100): fail(errors,'level 100 unreachable')
    return {'passed':not errors,'node_count':len(nodes),'reachable_count':len(reachable),'errors':errors}

def difficulty(row,cfg):
    errors=[];inputs=set(row.get('allowed_inputs',[]));forbidden=set(cfg['forbidden_inputs'])
    bad=sorted(inputs&forbidden)
    if bad: fail(errors,'spend-linked difficulty inputs: '+','.join(bad))
    samples=sorted(row.get('samples',[]),key=lambda x:x.get('level',0))
    if len(samples)<2: fail(errors,'insufficient difficulty samples')
    hp_only_run=0
    for a,b in zip(samples,samples[1:]):
        if b.get('level')!=a.get('level')+1: fail(errors,'difficulty levels must be contiguous')
        da=float(a.get('difficulty',0));db=float(b.get('difficulty',0))
        if da<=0 or db<=0: fail(errors,'difficulty must be positive')
        if da and db/da>float(cfg['max_step_ratio']): fail(errors,'difficulty spike exceeds bound at '+str(b.get('level')))
        changed_hp=float(b.get('hp_multiplier',0))>float(a.get('hp_multiplier',0))
        other=(float(b.get('spawn_pressure',0))>float(a.get('spawn_pressure',0)) or float(b.get('resource_pressure',0))>float(a.get('resource_pressure',0)))
        hp_only_run=hp_only_run+1 if changed_hp and not other else 0
        if hp_only_run>int(cfg['hp_only_increase_run_max']): fail(errors,'HP-only inflation run exceeds bound')
    return {'passed':not errors,'sample_count':len(samples),'errors':errors}

def save_versioning(row,cfg):
    errors=[];required=set(cfg['required_cases']);seen={c.get('name') for c in row.get('cases',[]) if c.get('passed') is True}
    miss=sorted(required-seen)
    if miss: fail(errors,'missing/passing save cases: '+','.join(miss))
    current=int(row.get('current_version',0));edges={(int(m['from']),int(m['to'])) for m in row.get('migrations',[])}
    for start in row.get('supported_prior_versions',[]):
        v=int(start);guard=0
        while v<current and guard<100:
            nxt=[b for a,b in edges if a==v and b>v]
            if not nxt: break
            v=min(nxt);guard+=1
        if v!=current: fail(errors,f'no migration path {start}->{current}')
    hashes=[x.get('sha256') for x in row.get('golden_fixtures',[])]
    if any(not HEX64.fullmatch(str(h or '')) for h in hashes) or len(hashes)!=len(set(hashes)): fail(errors,'invalid/duplicate golden fixture hashes')
    if row.get('corrupt_recovery')!='FAIL_CLOSED': fail(errors,'corrupt recovery must fail closed')
    return {'passed':not errors,'errors':errors}

def population(row,cfg):
    errors=[];agents=row.get('agents',[]);ids=[a.get('actor_id') for a in agents]
    if len(ids)!=len(set(ids)) or None in ids: fail(errors,'actor identities must be unique')
    if len(agents)>int(row.get('population_budget',0)): fail(errors,'population exceeds budget')
    routes={r.get('route_id'):r for r in row.get('routes',[])}
    for a in agents:
        r=routes.get(a.get('route_id'))
        if not r or len(r.get('path',[]))<2: fail(errors,'unresolvable route for '+str(a.get('actor_id')))
        if not a.get('save_reload_identity_preserved'): fail(errors,'identity not preserved '+str(a.get('actor_id')))
    if int(row.get('deadlocks',-1))!=0: fail(errors,'deadlocks must be zero')
    return {'passed':not errors,'population':len(agents),'errors':errors}

def action_arbitration(row,cfg):
    errors=[]
    for c in row.get('contexts',[]):
        if c.get('automatic') is not True: fail(errors,'context must be automatic '+str(c.get('id')))
        eligible=c.get('eligible',[]);priorities=[a.get('priority') for a in eligible]
        if len(priorities)!=len(set(priorities)): fail(errors,'priority tie '+str(c.get('id')))
        if not eligible: fail(errors,'empty eligible actions '+str(c.get('id')));continue
        expected=max(eligible,key=lambda a:a.get('priority',-10**9)).get('action')
        if c.get('selected')!=expected: fail(errors,'wrong selected action '+str(c.get('id')))
        for a in eligible:
            if not a.get('contact_authority') or not a.get('cancel_rule'): fail(errors,'missing authority/cancel rule '+str(c.get('id')))
    return {'passed':not errors,'context_count':len(row.get('contexts',[])),'errors':errors}

def motion_readiness(row,cfg):
    errors=[];sp=row.get('species',{})
    for name in cfg['species']:
        r=sp.get(name)
        if not r: fail(errors,'missing species '+name);continue
        for k in ('locomotion','work','combat'):
            if not r.get(k): fail(errors,f'{name} missing {k}')
    extra=sorted(set(sp)-set(cfg['species']))
    if extra: fail(errors,'unexpected companion species: '+','.join(extra))
    return {'passed':not errors,'species_count':len(sp),'errors':errors}

def transaction_security(row,cfg):
    errors=[];attempts=row.get('attempts',[]);seen=set();balance=row.get('initial_balance')
    for a in attempts:
        tid=a.get('transaction_id');debit=int(a.get('debit',0))
        if tid in seen and debit!=0: fail(errors,'duplicate transaction debited twice '+str(tid))
        if a.get('kind')=='stale_replay' and a.get('accepted'): fail(errors,'stale replay accepted')
        if debit<0: fail(errors,'negative debit')
        if balance is not None: balance-=debit
        if a.get('balance_after')!=balance: fail(errors,'balance mismatch '+str(tid))
        seen.add(tid)
    if not row.get('authority'): fail(errors,'transaction authority missing')
    if not row.get('rollback_defined'): fail(errors,'rollback undefined')
    return {'passed':not errors,'attempt_count':len(attempts),'errors':errors}

def liveops_clock(row,cfg):
    errors=[];required=set(cfg['required_cases']);seen=set()
    for c in row.get('cases',[]):
        seen.add(c.get('id'))
        if c.get('passed') is not True: fail(errors,'clock case failed '+str(c.get('id')))
        if int(c.get('duplicate_rewards',-1))!=0: fail(errors,'duplicate reward '+str(c.get('id')))
        if c.get('collision_resolved') is not True: fail(errors,'unresolved collision '+str(c.get('id')))
        if c.get('id')=='kill_switch' and c.get('kill_switch_effective') is not True: fail(errors,'kill switch ineffective')
    miss=sorted(required-seen)
    if miss: fail(errors,'missing clock cases: '+','.join(miss))
    return {'passed':not errors,'case_count':len(seen),'errors':errors}

def region_template(row,cfg):
    errors=[]
    for k in cfg['required']:
        if k not in row or row[k] in (None,[],{},''): fail(errors,'missing/empty region field '+k)
    return {'passed':not errors,'errors':errors}

def accessibility_device(row,cfg):
    errors=[]
    for k in cfg['required_checks']:
        if row.get(k) is not True: fail(errors,'accessibility/device check failed '+k)
    return {'passed':not errors,'errors':errors}

def physical_reconnaissance(row,cfg):
    errors=[]
    for k in cfg['required']:
        if k not in row: fail(errors,'missing physical recon field '+k)
    if row.get('non_certification') is not True: fail(errors,'early physical recon must be marked non_certification')
    if row.get('build_sha') and not HEX40.fullmatch(str(row['build_sha'])): fail(errors,'build_sha invalid')
    if int(row.get('duration_minutes',0))<=0: fail(errors,'duration must be positive')
    return {'passed':not errors,'errors':errors}

def external_capabilities(row,cfg):
    errors=[];allowed={'READY','UNVERIFIED','UNAVAILABLE','DEFERRED','MISSING_LOCAL'}
    for k,v in row.get('external',{}).items():
        st=v.get('state')
        if st not in allowed: fail(errors,'invalid external capability state '+k)
        if st=='READY' and not v.get('evidence'): fail(errors,'READY external capability lacks evidence '+k)
    return {'passed':not errors,'count':len(row.get('external',{})),'errors':errors}

FUNCS={'progression':progression,'difficulty':difficulty,'save_versioning':save_versioning,'population':population,'action_arbitration':action_arbitration,'motion_readiness':motion_readiness,'transaction_security':transaction_security,'liveops_clock':liveops_clock,'region_template':region_template,'accessibility_device':accessibility_device,'physical_reconnaissance':physical_reconnaissance}

def check(domain,row):
    contracts=load('V32_FORWARD_PREP_CONTRACTS.json')['contracts']
    if domain=='external_capabilities': return external_capabilities(row,contracts[domain])
    if domain not in FUNCS: return {'passed':False,'errors':['unknown domain '+domain]}
    return FUNCS[domain](row,contracts[domain])

def validate_all():
    can=load('V32_FORWARD_PREP_CANARIES.json');results={};errors=[]
    for domain,row in can.items():
        if domain=='schema_version': continue
        results[domain]=check(domain,row)
        if not results[domain]['passed']: errors += [domain+': '+e for e in results[domain]['errors']]
    cap=load('CAPABILITY_STATUS.json');results['external_capabilities']=check('external_capabilities',cap)
    if not results['external_capabilities']['passed']: errors += ['external_capabilities: '+e for e in results['external_capabilities']['errors']]
    return {'passed':not errors,'domain_count':len(results),'results':results,'errors':errors}

def fixture(domain):
    if domain=='external_capabilities': return check(domain,load('CAPABILITY_STATUS.json'))
    can=load('V32_FORWARD_PREP_CANARIES.json')
    if domain not in can: return {'passed':False,'errors':['missing fixture domain '+domain]}
    return check(domain,can[domain])

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate')
    c=sub.add_parser('check');c.add_argument('domain');c.add_argument('record')
    f=sub.add_parser('fixture');f.add_argument('domain')
    a=ap.parse_args()
    if a.cmd=='validate': out=validate_all()
    elif a.cmd=='fixture': out=fixture(a.domain)
    else: out=check(a.domain,json.loads(Path(a.record).read_text()))
    print(json.dumps(out,indent=2));raise SystemExit(0 if out.get('passed') else 2)
if __name__=='__main__':main()
