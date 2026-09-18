#!/usr/bin/env python3
from __future__ import annotations
import argparse,fnmatch,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'Docs/Production/RUNTIME_DEPENDENCY_OBSERVATIONS.json';GRAPH=ROOT/'Docs/Production/DEPENDENCY_GRAPH.json'
def load():return json.loads(DATA.read_text())
def validate(data=None):
    data=data or load();errors=[];p=data.get('policy',{})
    if data.get('schema_version')!=1:errors.append('schema_version must be 1')
    if p.get('learned_edges_are_additive_only') is not True:errors.append('learned edges must be additive only')
    if p.get('static_mandatory_coverage_may_be_removed_automatically') is not False:errors.append('learned observations may not auto-remove static coverage')
    for i,e in enumerate(data.get('edges',[])):
        for k in ('path_pattern','affected_task','suites','observation_count','distinct_sources'):
            if k not in e:errors.append(f'edge {i} missing {k}')
        if not isinstance(e.get('suites',[]),list):errors.append(f'edge {i} suites must be list')
    return {'passed':not errors,'errors':errors,'edge_count':len(data.get('edges',[]))}
def validate_trace(trace:dict):
    errors=[];graph=json.loads(GRAPH.read_text()).get('tasks',{})
    if trace.get('schema_version')!=1:errors.append('trace schema_version must be 1')
    source=str(trace.get('source_sha',''))
    if not re.fullmatch(r'[0-9a-f]{40}',source):errors.append('trace source_sha must be exact 40-char SHA')
    task=str(trace.get('task_id','')).upper()
    if not re.fullmatch(r'T[0-9]{2}',task) or task not in graph:errors.append('trace task_id must be a known TNN task')
    observer=str(trace.get('observer','')).strip()
    if not observer:errors.append('trace observer is required')
    events=trace.get('events')
    if not isinstance(events,list) or not events:errors.append('trace events must be a non-empty list');events=[]
    normalized=[]
    allowed_kinds={'read','write','signal','resource_load','scene_instantiation','contract_use','runtime_call'}
    for i,event in enumerate(events):
        if not isinstance(event,dict):errors.append(f'event {i} must be object');continue
        path=str(event.get('path',''))
        affected=str(event.get('affected_task','')).upper()
        suites=event.get('suites',[]);kind=str(event.get('kind',''))
        if not path.startswith('HavenlineGodot/'):errors.append(f'event {i} path must be observed HavenlineGodot runtime path')
        if affected not in graph:errors.append(f'event {i} affected_task must be known task')
        if kind not in allowed_kinds:errors.append(f'event {i} kind invalid')
        if not isinstance(suites,list) or not suites or not all(isinstance(x,str) and x.strip() for x in suites):errors.append(f'event {i} suites must be non-empty string list')
        normalized.append({'path':path,'affected_task':affected,'suites':sorted(set(suites)) if isinstance(suites,list) else [],'kind':kind})
    return {'passed':not errors,'errors':errors,'source_sha':source,'task_id':task,'observer':observer,'events':normalized,'observation_is_additive_only':True,'static_coverage_removal_forbidden':True}
def learned_impact(files:list[str],data=None):
    data=data or load();p=data['policy'];tasks=set();suites=set();matched=[]
    for e in data.get('edges',[]):
        if int(e.get('observation_count',0))<int(p['minimum_observations_for_enforcement']):continue
        if int(e.get('distinct_sources',0))<int(p['minimum_distinct_sources']):continue
        if any(fnmatch.fnmatch(path,e['path_pattern']) for path in files):
            tasks.add(e['affected_task']);suites.update(e.get('suites',[]));matched.append(e)
    return {'impacted_tasks':sorted(tasks),'required_suites':sorted(suites),'matched_edges':matched,'coverage_mode':'ADDITIVE_ONLY'}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');q=sub.add_parser('impact');q.add_argument('files',nargs='+');t=sub.add_parser('trace');t.add_argument('file');a=ap.parse_args()
    if a.cmd=='validate':r=validate()
    elif a.cmd=='impact':r=learned_impact(a.files)
    else:r=validate_trace(json.loads(Path(a.file).read_text()))
    print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
