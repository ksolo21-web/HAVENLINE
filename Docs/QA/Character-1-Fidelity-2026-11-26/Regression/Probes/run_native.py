"""Exercise all previously accepted native Level 1 suites under private save homes."""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

SUITES = (
    'qa_storage_house_art','qa_field_minerals','qa_field_mineral_art','qa_mining_return',
    'tests/world_landscape_qa','qa_field_progression','qa_field_inventory','qa_field_stock_limits',
    'qa_field_save','qa_field_purchase_scene','qa_world_lifecycle','qa_encounter_waves',
    'qa_world_session_resume','qa_world_orbit','qa_world_perimeter','qa_field_tracks_tower',
    'qa_field_environment','qa_field_forest','qa_world_combat','qa_field_landmark_scale',
    'qa_tree_return','qa_field_pack_bounds',
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def execute(project, name, output):
    base=name.split('/')[-1]
    result=[]
    with tempfile.TemporaryDirectory(prefix='hvn-fidelity-native-') as private:
        env=os.environ.copy()
        env.update({k:str(Path(private)/v) for k,v in [
            ('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache')]})
        env.update(LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        primary=['godot','--headless','--audio-driver','Dummy','--fixed-fps','60',
                 '--audio-output-latency','5','--frame-delay','5',
                 '--path',str(project),'--script','res://'+name+'.gd']
        cmds=[primary]
        if base=='qa_field_purchase_scene':
            cmds.append(primary+['--','--native-resume-final'])
        for i,command in enumerate(cmds):
            proc=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
            text=proc.stdout.decode()
            log=output/f'{base}-{i+1}.log'
            log.write_text(text)
            metrics = []
            for line in text.splitlines():
                start=line.find('{')
                if start<0:continue
                try:metrics.append(json.loads(line[start:]))
                except ValueError:pass
            errors=[l for l in text.splitlines() if re.search('SCRIPT ERROR|Parse Error|ERROR:',l)]
            warnings=[l for l in text.splitlines() if l.startswith('WARNING:')]
            result.append(dict(exit_code=proc.returncode,errors=errors,warnings=warnings,
                               log=log.name,log_sha256=digest(log),summary=metrics))
        return base,result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project',type=Path);ap.add_argument('commit');ap.add_argument('out',type=Path)
    args=ap.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',args.commit)
    args.out.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        rows=dict(executor.map(lambda name:execute(args.project,name,args.out),SUITES))
    accepted=all(r['exit_code']==0 and not r['errors'] and not r['warnings'] for runs in rows.values() for r in runs)
    result=dict(source=args.commit,scene='res://field_opening.tscn',
                engine=subprocess.check_output(['godot','--version'],text=True).strip(),
                suites=len(rows),native_runs=sum(map(len,rows.values())),
                tests=rows,passed=accepted)
    (args.out/'Native-results.json').write_text(json.dumps(result,indent=2)+'\n')
    for k,rows in result['tests'].items():
        print(k,[(r['exit_code'],len(r['errors']),len(r['warnings'])) for r in rows])
    if not accepted:raise SystemExit(1)

if __name__=='__main__':
    main()
