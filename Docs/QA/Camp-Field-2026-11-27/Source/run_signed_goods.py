"""Exercise gameplay from the GODOT resources embedded in this signed Android APK."""
import hashlib,json,tempfile,subprocess,os,shutil,sys
from pathlib import Path
import zipfile
here=Path(__file__).resolve().parent
pack=Path(sys.argv[1]); output=Path(sys.argv[2]); fixtures=here/'Fixtures'
out={}
for name,fixture,modes in [
 ('ledger', 'Build8-paid-workshops.json',['manual','cold','bulk']),
 ('connected','Build9-settled.json',['connected']),
]:
 with tempfile.TemporaryDirectory(prefix='havenline-l1-v3-signed13-') as td:
  profile=Path(td);(profile/'L1-DISPOSABLE').write_text('HAVENLINE-ALFRED-V3-DISPOSABLE\n');cases=[]
  for i,mode in enumerate(modes):
   if mode!='cold':shutil.copy2(fixtures/fixture,profile/'field-inventory-v1.json')
   env=dict(os.environ, XDG_DATA_HOME=td+'/data',XDG_CACHE_HOME=td+'/cache',XDG_CONFIG_HOME=td+'/config',LP_NUM_THREADS='1')
   cmd=['godot','--headless','--audio-driver','Dummy','--fixed-fps','60','--main-pack',str(pack),'--script',str(here/'check_signed_goods.gd'),'--','--l1-disposable-profile='+td,'--personal-goods='+mode]
   p=subprocess.run(cmd,capture_output=True,env=env,cwd='/tmp',text=True,timeout=135)
   text=p.stdout+p.stderr
   log=output.parent/f'Signed-{name}-{mode}.log';log.write_text(text)
   if p.returncode or any(x in text for x in ['SCRIPT ERROR','Parse Error','ERROR:']):raise RuntimeError(str(log)+': '+text[-1100:])
   rows=[]
   for line in text.splitlines():
    if '{' in line:
     try:rows.append(json.loads(line[line.index('{'):]))
     except ValueError:pass
   assert rows
   cases.append(dict(mode=mode,exit=p.returncode,results=rows))
  out[name]=cases
output.write_text(json.dumps(out,indent=2)+'\n')
