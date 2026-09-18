#!/usr/bin/env python3
"""Executable case adapter for the unchanged canonical save-state runner."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CASES={'fresh_save','existing_current_save','previous_version_save','interrupted_save','reload','migration','rollback_recovery'}
def main():
 if len(sys.argv)!=2 or sys.argv[1] not in CASES: raise SystemExit('Unknown canonical save case')
 candidate=os.environ.get('HAVENLINE_CANDIDATE','');case=sys.argv[1]
 if not re.fullmatch('[0-9a-f]{40}',candidate) or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=candidate: raise SystemExit('Exact source binding required')
 subprocess.run(['git','diff','--exit-code','HEAD','--','HavenlineGodot/scripts','HavenlineGodot/tests','tools/havenline/task10'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
 godot=shutil.which(os.environ.get('GODOT','Godot_v4.7.2-stable_linux.x86_64'))
 if not godot or subprocess.check_output([godot,'--version'],text=True).strip()!='4.7.2.stable.official.ed1daf0bf': raise SystemExit('Pinned Godot required')
 run=subprocess.run([godot,'--headless','--audio-driver','Dummy','--path',str(ROOT/'HavenlineGodot'),'--script',str(ROOT/'tools/havenline/task10/save_matrix_cases.gd'),'--',case],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 print(run.stdout,end='')
 reports=[json.loads(l) for l in run.stdout.splitlines() if l.startswith('{')]
 valid=run.returncode==0 and len(reports)==1 and reports[0].get('case')==case and reports[0].get('passed') is True and not reports[0].get('failures') and all(x.get('passed') is True for x in reports[0].get('checks',[]))
 valid=valid and not any(x in run.stdout for x in ['SCRIPT ERROR','Parse Error','ERROR:','ObjectDB instances were leaked'])
 print(json.dumps({'candidate_commit':candidate,'task_id':'T10','case':case,'executed':True,'passed':valid,'script_sha256':hashlib.sha256((ROOT/'tools/havenline/task10/save_matrix_cases.gd').read_bytes()).hexdigest(),'log_sha256':hashlib.sha256(run.stdout.encode()).hexdigest()}))
 raise SystemExit(0 if valid else 1)
if __name__=='__main__':main()
