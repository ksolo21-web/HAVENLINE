"""Verify new environment resources in the exported APK, not merely the source."""
from pathlib import Path,PurePosixPath
from zipfile import ZipFile
import argparse,configparser,json,hashlib

def inspect(path):
 with ZipFile(path) as z:
  names=z.namelist();manifest=json.loads(z.read('assets/assets/environment_v2/manifest.json').rstrip(b'\0'))
  checks={'fourteen_environment_assets_registered':len(manifest['assets'])==14};targets={}
  for a in manifest['assets']:
   name=a['name'];good=False
   for suffix in ['.import','.remap']:
    record='assets/assets/environment_v2/'+name+'.glb'+suffix
    if names.count(record)!=1:continue
    try:
     text=z.read(record).decode().rstrip('\0')
     if '\0' in text:continue
     c=configparser.ConfigParser(interpolation=None,strict=True);c.read_string(text)
     target=json.loads(c.get('remap','path'));p=PurePosixPath(target.removeprefix('res://'))
     if not target.startswith('res://.godot/imported/') or '..' in p.parts or '\\' in str(p):continue
     actual='assets/'+str(p)
     if names.count(actual)!=1 or z.getinfo(actual).file_size<16:continue
     if z.read(actual)[:4] not in [b'RSCC',b'RSRC']:continue
     targets[name]=actual;good=True
    except (KeyError,ValueError,TypeError,UnicodeError,configparser.Error):pass
   checks['imported_model_'+name]=good
  checks['environment_shader_packaged']=any(x.startswith('assets/shaders/evergreen.gdshader') for x in names)
  checks['approval_not_fabricated']=manifest['production_visual_approval'] is False
 return {'apk_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checks':checks,'targets':targets,'passed':all(checks.values()),'physical_device_performance_verified':False,'visual_quality_score':None}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=inspect(a.apk);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['passed'] else 1)
