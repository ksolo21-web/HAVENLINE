#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from parallel_preparation_planner import classify
from external_readiness import evaluate as external_readiness
ROOT=Path(__file__).resolve().parents[3];DOCS=ROOT/'Docs'/'Production'
def load(n): return json.loads((DOCS/n).read_text())
def source_sha():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:return 'UNKNOWN'
def roadmap_row(task,roadmap):
    return next((r for r in roadmap.get('immediate_parallel_prep',[]) if task in r.get('tasks',[])),None)
def render(task):
    task=task.upper();n=int(task[1:])
    if n<12 or n>70: raise ValueError('future prep packet supports T12-T70; T11 uses its real task packet')
    graph=load('DEPENDENCY_GRAPH.json');roadmap=load('V32_FORWARD_PREP_ROADMAP.json');plan=classify(task);row=roadmap_row(task,roadmap)
    if row is None: raise ValueError('task missing from forward prep roadmap: '+task)
    canaries=roadmap.get('task_canary_domains',{}).get(task,[]);ext=external_readiness();required_caps=[x for x in ext['rows'] if task in x['required_by']];g=graph['tasks'][task]
    lines=[
      '# HAVENLINE V3.2 future-preparation packet — '+task,'',
      '## Identity',
      '- Task: '+task+' — '+g['name'],
      '- Generated from source: '+source_sha(),
      '- Current lifecycle: '+g['status'],
      '- Parallel-preparation classification: '+plan['classification'],
      '- Prep lane: '+row['lane'],
      '- PREPARATION ONLY. This packet is not lifecycle authority, does not grant ownership, cannot integrate runtime and cannot approve the task.','',
      '## Dependency state'
    ]
    for dep,state in plan['dependency_status'].items(): lines.append('- '+dep+': '+state)
    lines += ['', '## Safe work that can be completed ahead of activation']
    for x in row['deliverables']: lines.append('- '+x)
    lines += ['', '## Forbidden until the real task graduates']
    for x in row['forbidden']: lines.append('- '+x)
    lines += ['', '## Deterministic prep canaries']
    if canaries:
        for domain in canaries: lines.append('- '+domain+': python3 tools/havenline/production/v32_forward_prep_harness.py fixture '+domain)
    else: lines.append('- No task-specific synthetic domain canary; use the task sentinel/profile and applicable shared matrices.')
    lines += ['', '## External capability look-ahead']
    if required_caps:
        for c in required_caps: lines.append('- '+c['capability']+': '+c['state']+' / '+c['phase']+'; prepare by '+c['prepare_by']+'; required by '+', '.join(c['required_by'])+'.')
    else: lines.append('- No external/hardware capability is directly required by this task.')
    lines += [
      '', '## Graduation boundary',
      '- Current safe work: '+', '.join(plan['safe_work']),
      '- When dependencies are APPROVED and the canonical workstream exists: python3 tools/havenline/production/task_graduation_gate.py '+task+' --target ASSIGNED',
      '- Authoritative runtime build still requires the full V3.2 BUILDING_ISOLATED graduation package.','',
      '## Quality rule',
      '- Every applicable mandatory critic dimension remains strictly >9.0 unrounded; target 10/10; no averaging; zero unresolved mandatory defects.',
      '- Preparation removes uncertainty and builds proof machinery early; it never waives final gameplay, visual, performance, security, device or physical certification requirements.',''
    ]
    return '\n'.join(lines)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('task');ap.add_argument('--output');a=ap.parse_args();text=render(a.task)
    if a.output:
        p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    print(text)
if __name__=='__main__':main()
