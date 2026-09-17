#!/usr/bin/env python3
from __future__ import annotations
import argparse,fnmatch,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];DATA=ROOT/'Docs/Production/RUNTIME_DEPENDENCY_OBSERVATIONS.json'
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
def learned_impact(files:list[str],data=None):
    data=data or load();p=data['policy'];tasks=set();suites=set();matched=[]
    for e in data.get('edges',[]):
        if int(e.get('observation_count',0))<int(p['minimum_observations_for_enforcement']):continue
        if int(e.get('distinct_sources',0))<int(p['minimum_distinct_sources']):continue
        if any(fnmatch.fnmatch(path,e['path_pattern']) for path in files):
            tasks.add(e['affected_task']);suites.update(e.get('suites',[]));matched.append(e)
    return {'impacted_tasks':sorted(tasks),'required_suites':sorted(suites),'matched_edges':matched,'coverage_mode':'ADDITIVE_ONLY'}
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True);sub.add_parser('validate');q=sub.add_parser('impact');q.add_argument('files',nargs='+');a=ap.parse_args();r=validate() if a.cmd=='validate' else learned_impact(a.files);print(json.dumps(r,indent=2));raise SystemExit(0 if r.get('passed',True) else 2)
if __name__=='__main__':main()
