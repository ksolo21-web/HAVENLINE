#!/usr/bin/env python3
"""Collect the complete frozen domain before returning red on any case failure."""
import argparse
import json
import os
import subprocess
from pathlib import Path
import verify_rendered_clearance_domain as verifier


def collect(repo, output, source, engine, workflow):
    output.mkdir(parents=True, exist_ok=False)
    project = repo/'HavenlineGodot'
    capture_sha = verifier.sha256(project/'tests/capture_task10_world_transform.gd')
    view_sha = verifier.sha256(project/'scripts/world_transform_view.gd')
    if view_sha != '5067ea967ea527cb28a4d5df5f4a5bd4cca8bf5dad393c4b6ca326a9897d8561':
        raise ValueError('Strategy A product blob changed')
    verifier_sha = verifier.sha256(Path(verifier.__file__))
    workflow_sha = verifier.sha256(repo/workflow)
    resource_sha = verifier.sha256(project/'assets/world_transform_v1/resource_symbols.tres')
    matrix=json.loads((repo/'Docs/Production/DEVICE_LAYOUT_MATRIX.json').read_text())
    if {r['id']:tuple(r['logical_size']) for r in matrix['states']} != verifier.DEVICES:
        raise ValueError('independent device domain disagrees with canonical matrix')
    summaries=[]
    for profile,(logical,physical,scale) in verifier.PROFILES.items():
        folder=output/profile; folder.mkdir()
        command=['xvfb-run','-a','-s',f'-screen 0 {physical[0]}x{physical[1]}x24',engine,
                 '--path',str(project),'--rendering-method','mobile','--rendering-driver','vulkan',
                 '--audio-driver','Dummy','--resolution',f'{physical[0]}x{physical[1]}',
                 '--script','res://tests/capture_task10_world_transform.gd','--',
                 f'--candidate={source}',f'--domain-profile={profile}',f'--device-id={profile}',
                 f'--width={physical[0]}',f'--height={physical[1]}',
                 f'--logical-width={logical[0]}',f'--logical-height={logical[1]}',
                 f'--readability-scale={scale}',f'--out={folder}',f'--product-view-sha256={view_sha}',
                 f'--probe-source={source}',f'--probe-capture-sha256={capture_sha}',
                 f'--probe-verifier-sha256={verifier_sha}',f'--probe-workflow-sha256={workflow_sha}']
        if profile=='native4k_anchors': command.append('--native4k-anchors')
        (folder/'command.json').write_text(json.dumps(command,indent=2))
        try:
            with (folder/'capture.log').open('w') as log:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=480)
            status=result.returncode
        except subprocess.TimeoutExpired:
            status=124
        (folder/'capture-exit.txt').write_text(str(status)+'\n')
        summary={'profile':profile,'capture_exit':status,'passed':False}
        try:
            report=verifier.verify(folder,folder/'manifest.json',folder/'masks',source,view_sha,
                                   'candidate',source,capture_sha,verifier_sha,workflow_sha,resource_sha,profile)
            (folder/'rendered-clearance.json').write_text(json.dumps(report,indent=2)+'\n')
            summary.update(case_count=len(report['rows']),failure_count=report['failure_count'],
                           report_sha256=verifier.sha256(folder/'rendered-clearance.json'),
                           passed=status==0 and report['passed'])
            log=(folder/'capture.log').read_text(errors='replace')
            if any(marker in log for marker in ('SCRIPT ERROR','Parse Error','ObjectDB instances were leaked')):
                summary.update(passed=False,error='engine_error_in_log')
        except (ValueError,TypeError,KeyError,OSError) as exc:
            summary['error']=f'{type(exc).__name__}: {exc}'
        summaries.append(summary)
        # Retain partial progress immediately; never treat it as completion.
        (output/'progress.json').write_text(json.dumps(summaries,indent=2)+'\n')
    passed=all(row['passed'] for row in summaries) and sum(row.get('case_count',0) for row in summaries)==650
    result={'contract':verifier.CONTRACT,'source':source,'view_sha256':view_sha,
            'capture_sha256':capture_sha,'verifier_sha256':verifier_sha,'workflow_sha256':workflow_sha,
            'profiles':summaries,'expected_cases':650,'domain_complete':len(summaries)==19 and
            sum(row.get('case_count',0) for row in summaries)==650,'passed':passed,'task_approved':False}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--output',type=Path,required=True)
    p.add_argument('--source',required=True);p.add_argument('--engine',required=True);p.add_argument('--workflow',required=True)
    a=p.parse_args()
    result=collect(a.repo.resolve(),a.output.resolve(),a.source,a.engine,a.workflow)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
