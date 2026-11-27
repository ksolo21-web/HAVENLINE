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
import time

SUITES = (
    'qa_storage_house_art','qa_field_minerals','qa_field_mineral_art','qa_mining_return',
    'tests/world_landscape_qa','qa_field_progression','qa_field_inventory','qa_field_stock_limits',
    'qa_field_save','qa_field_purchase_scene','qa_world_lifecycle','qa_encounter_waves',
    'qa_world_session_resume','qa_world_orbit','qa_world_perimeter','qa_field_tracks_tower',
    'qa_field_environment','qa_field_forest','qa_world_combat','qa_field_landmark_scale',
    'qa_tree_return','qa_field_pack_bounds','qa_field_counter','qa_field_lakeshore',
    'qa_field_processors','qa_field_survivor','qa_field_owl',
    'tests/qa_field_run_input','qa_field_auto_gates','tests/qa_spoke_sweep','qa_orbit_camera','qa_wolf_attack',
    'qa_camp_healing','tests/qa_field_navigation','tests/qa_field_touch_resume','tests/qa_build_offer_route','tests/qa_worker_supply','tests/qa_production_balances','tests/qa_field_audio_playback',
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_manifest(project, manifest, commit):
    receipt = json.loads(manifest.read_text())
    if receipt["commit"] != commit:
        raise RuntimeError("Manifest belongs to another revision")
    for name, expected in receipt["files"].items():
        if digest(project / name) != expected:
            raise RuntimeError("Source changed: " + name)
    return {"sha256":digest(manifest),"checked_files":len(receipt["files"])}

def execute(project, name, output):
    base=name.split('/')[-1]
    result=[]
    with tempfile.TemporaryDirectory(prefix='havenline-l1-v3-native-') as private:
        env=os.environ.copy()
        env.update({k:str(Path(private)/v) for k,v in [
            ('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache')]})
        env.update(LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        primary=['godot','--headless','--audio-driver','Dummy','--fixed-fps','60',
                 '--audio-output-latency','5','--frame-delay','5',
                 '--path',str(project),'--script','res://'+name+'.gd']
        if base == 'qa_field_audio_playback':
            primary = ['godot','--headless','--audio-driver','Dummy','--max-fps','90','--path',str(project),'--script','res://'+name+'.gd']
        if base in ('qa_field_survivor','qa_field_auto_gates','qa_worker_supply','qa_build_offer_route'):
            (Path(private)/'L1-DISPOSABLE').write_text('HAVENLINE-ALFRED-V3-DISPOSABLE\n')
            primary += ['--','--l1-disposable-profile=' + private]
        cmds=[primary]
        if base=='qa_build_offer_route':
            cmds=[primary+['--plot6-'+phase] for phase in ('start','resume','end')]
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
    ap.add_argument('--manifest',type=Path)
    ap.add_argument('--jobs',type=int,choices=(1,2),default=1)
    ap.add_argument('--only',nargs='+',choices=SUITES)
    ap.add_argument('--resume',action='store_true',help='Reuse verified passing receipts from this source and runner.')
    args=ap.parse_args()
    if (args.only or args.resume) and not args.manifest:
        ap.error('Partial or resumed runs require a verified manifest.')
    before = verify_manifest(args.project,args.manifest,args.commit) if args.manifest else None
    assert args.commit == 'working-tree' or re.fullmatch('[0-9a-f]{40}',args.commit)
    args.out.mkdir(parents=True,exist_ok=True)
    stamp = {'commit':args.commit,'manifest':before,'runner':digest(Path(__file__))}
    receipts = args.out / 'Receipts'
    receipts.mkdir(exist_ok=True)
    def run_suite(name):
        base = name.split('/')[-1]
        receipt = receipts / (base + '.json')
        if args.resume and receipt.exists():
            cached = json.loads(receipt.read_text())
            if cached['stamp'] == stamp and cached['passed'] and all(digest(args.out / r['log']) == r['log_sha256'] for r in cached['runs']):
                return base,cached['runs']
        pressure = Path('/sys/fs/cgroup/memory.current')
        while pressure.exists() and int(pressure.read_text()) > int(14.2 * 1024**3):
            time.sleep(3)
        key, runs = execute(args.project,name,args.out)
        passed = all(r['exit_code']==0 and not r['errors'] and not r['warnings'] for r in runs)
        if args.manifest and verify_manifest(args.project,args.manifest,args.commit) != before:
            raise RuntimeError('Source changed during '+name)
        receipt.write_text(json.dumps({'stamp':stamp,'passed':passed,'runs':runs},indent=2)+'\n')
        return key,runs
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        rows=dict(executor.map(run_suite,args.only or SUITES))
    accepted=all(r['exit_code']==0 and not r['errors'] and not r['warnings'] for runs in rows.values() for r in runs)
    result=dict(source=args.commit,scene='res://field_opening.tscn',
                engine=subprocess.check_output(['godot','--version'],text=True).strip(),
                suites=len(rows),native_runs=sum(map(len,rows.values())),
                tests=rows,passed=accepted)
    if args.manifest:
        if verify_manifest(args.project,args.manifest,args.commit) != before:
            raise RuntimeError("Manifest changed during run")
        result["verified_source_before_and_after"] = before
    if not args.only:
        (args.out/'Native-results.json').write_text(json.dumps(result,indent=2)+'\n')
    for k,rows in result['tests'].items():
        print(k,[(r['exit_code'],len(r['errors']),len(r['warnings'])) for r in rows])
    if not accepted:raise SystemExit(1)

if __name__=='__main__':
    main()
