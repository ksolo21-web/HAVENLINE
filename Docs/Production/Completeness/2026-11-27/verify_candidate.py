#!/usr/bin/env python3
"""Reproduce focused planning/tool tests and preservation checks; no game approval."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import pathlib
import re
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[4]
PKG='Docs/Production/Completeness/2026-11-27/'
BASE='fd2e12c8734f49cda7eb3bbf97887406bd03a704'
ALLOWED={
 'AGENTS.md','BUILD_GAME.md','REPOSITORY_INDEX.md',
 'Docs/Production/COMPLETENESS_STANDARD.md','Docs/Production/CURRENT_GAMEPLAY_SOURCE.json',
 'Docs/Production/WHOLE_GAME_COMPLETENESS.json','Docs/Production/DEVICE_LAYOUT_MATRIX.json',
 'Docs/Production/HAVENLINE_BUILD_PLAN_V2.md','Docs/Production/TASK_PACKET_TEMPLATE.md',
 'Docs/Production/RESOURCE_TOOL_ACTOR_STANDARD.md',
 'tools/havenline/production/completeness.py','tools/havenline/production/device_matrix.py',
 'tools/havenline/production/task_packet.py','tools/havenline/production/resource_actor_contract.py',
 'tools/havenline/production/closure_validator.py',
 'tools/havenline/production/tests/test_completeness.py',
 'tools/havenline/production/tests/test_resource_actor_contract.py',
 'tools/havenline/production/tests/test_closure_resource_actor.py'}

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def changed():
    return sorted(set(git('diff','--name-only',BASE).decode().splitlines()) |
                  set(git('ls-files','--others','--exclude-standard').decode().splitlines()))

def digest(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def run(command):
    p=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    match=re.search(r'Ran (\d+) tests?',p.stdout)
    return {'command':command,'returncode':p.returncode,'passed':p.returncode==0,
            'test_count':int(match.group(1)) if match else None,'output':p.stdout}

def scope():
    paths=changed();checks=[]
    def check(name,passed,detail=None):checks.append({'id':name,'passed':bool(passed),'detail':detail})
    unexpected=[p for p in paths if p not in ALLOWED and not p.startswith(PKG)]
    check('only_allowlisted_plan_tool_and_review_paths',not unexpected,unexpected)
    missing=[p for p in paths if not (ROOT/p).is_file() or (ROOT/p).is_symlink()]
    check('no_deletion_or_symlink',not missing,missing)
    forbidden=[p for p in paths if p.endswith('.pyc') or '__pycache__' in p]
    check('no_generated_python_cache',not forbidden,forbidden)
    protected=['DEPENDENCY_GRAPH.json','WORKSTREAM_REGISTRY.json','PATH_OWNERSHIP.json',
       'APPROVAL_INVALIDATIONS.json','REFERENCE_ACCEPTANCE_POLICY.json','REFERENCE_STYLE_LOCK.json',
       'RESOURCE_ACTION_REGISTRY.json','ACTOR_CAPABILITY_MATRIX.json','ANIMATION_ACTION_MATRIX.json',
       'POST_LAUNCH_ROADMAP.md','CRITIC_MATRIX.json','task-gates.json']
    records=[]
    for name in protected:
        rel='Docs/Production/'+name;expected=git('show',BASE+':'+rel)
        records.append({'path':rel,'sha256':digest(rel),'unchanged':(ROOT/rel).read_bytes()==expected})
    check('protected_authorities_byte_exact',all(r['unchanged'] for r in records),records)
    graph=json.loads((ROOT/'Docs/Production/DEPENDENCY_GRAPH.json').read_text())['tasks']
    check('70_authentic_definitions_preserved',set(graph)=={f'T{i:02}' for i in range(1,71)},len(graph))
    task_edits=[p for p in paths if re.match(r'Docs/Production/(?:T\d{2}/|Evidence/T\d{2}/)',p)]
    check('frozen_task_directories_and_canonical_packets_unchanged',not task_edits,task_edits)
    for label,prefix in [('runtime','Havenline'),('archive','Docs/RepositoryArchive/'),
                         ('reference_media','Docs/Design/'),('prior_reference_package','Docs/Production/ReferenceRefresh/'),
                         ('prior_depth_package','Docs/Production/GameplayDepth/'),('workflows','.github/')]:
        edits=[p for p in paths if p.startswith(prefix)]
        check(label+'_unchanged',not edits,edits)
    check('operational_workflows_remain_absent',not git('ls-tree','--name-only','HEAD','.github').strip())
    # Stage first. Any whitespace diagnostic remains visible and blocks this new
    # package; no exceptions or broad suppression of git diagnostics are used.
    staged=subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    unstaged=subprocess.run(['git','diff','--check'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    check('staged_and_unstaged_whitespace_clean',all(p.returncode==0 and not p.stdout and not p.stderr for p in (staged,unstaged)),
          {'staged_returncode':staged.returncode,'staged_stdout':staged.stdout,'staged_stderr':staged.stderr,
           'unstaged_returncode':unstaged.returncode,'unstaged_stdout':unstaged.stdout,'unstaged_stderr':unstaged.stderr})
    return {'scope':'Local preservation and bounded change scope; remote publication checked separately',
       'base_commit':BASE,'passed':all(c['passed'] for c in checks),'checks':checks,
       'checks_passed':sum(c['passed'] for c in checks),'checks_required':len(checks),
       'changed_paths':paths,'runtime_approval_allowed':False}

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'all'
    if mode not in {'all','scope'}:raise SystemExit('all | scope')
    if mode=='all':
        commands=[[sys.executable,'tools/havenline/production/completeness.py','check'],
                  [sys.executable,'tools/havenline/production/gameplay_depth.py','check']]
        for name in ['test_completeness.py','test_gameplay_depth.py','test_resource_actor_contract.py',
                     'test_closure_resource_actor.py','test_reference_acceptance.py']:
            commands.append([sys.executable,'-m','unittest','discover','-s','tools/havenline/production/tests','-p',name,'-v'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(run,commands))
        raw={'scope':'Focused plan/declaration/closure regression checks, not game execution',
             'runtime_tested':False,'runs':runs,
             'source_hashes':{p:digest(p) for p in sorted(ALLOWED) if (ROOT/p).is_file()}}
        raw_path=ROOT/PKG/'Review/BUILDER_VALIDATION_RAW.json';raw_path.parent.mkdir(exist_ok=True)
        raw_path.write_text(json.dumps(raw,indent=2)+'\n')
        validation={'passed':all(r['passed'] for r in runs),'command_groups':len(runs),
              'command_groups_passed':sum(r['passed'] for r in runs),
              'unittest_methods':sum(r['test_count'] or 0 for r in runs),
              'raw_evidence':'Review/BUILDER_VALIDATION_RAW.json','raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
              'runtime_approval_allowed':False,'runtime_tested':False,'game_score':None,
              'scope':'Planning/tooling validation only; final independent freeze review is separate'}
        (ROOT/PKG/'VALIDATION.json').write_text(json.dumps(validation,indent=2)+'\n')
        print(json.dumps(validation))
    result=scope();(ROOT/PKG/'SCOPE_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'checks','changed_paths'}}))
    if not result['passed'] or (mode=='all' and not validation['passed']):raise SystemExit(1)

if __name__=='__main__':main()
