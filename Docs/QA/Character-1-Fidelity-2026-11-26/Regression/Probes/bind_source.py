"""Independently verify the working files, manifest and frozen Git objects."""
from pathlib import Path
import hashlib,json,subprocess,sys
project,repo,manifest,destination=map(Path,sys.argv[1:])
m=json.loads(manifest.read_text()); rev=m['commit'];prefix='HavenlineLevel1/'
cmd=['git','-C',str(repo)]
objects={}
for entry in subprocess.check_output(cmd+['ls-tree','-r','-z',rev,prefix]).split(b'\0'):
 if not entry:continue
 metadata,filename=entry.split(b'\t',1); objects[filename.decode()]=metadata.split()[-1].decode()
assert len(m['files'])>200
stage=[]
for name,expected in m['files'].items():
 contents=(project/name).read_bytes(); assert hashlib.sha256(contents).hexdigest()==expected,name
 actual=hashlib.sha1(b'blob '+str(len(contents)).encode()+b'\0'+contents).hexdigest()
 path=prefix+name
 if path in objects:
  assert actual==objects[path],name
 else:
  assert name=='assets/studio/hearth_trial_02.glb'
  part_prefix=prefix+'assets/studio/parts/hearth_trial_02.part'
  parts=[objects[s] for s in sorted(objects) if s.startswith(part_prefix)]
  assert parts
  baked=b''.join(subprocess.check_output(cmd+['cat-file','blob',id]) for id in parts)
  assert baked==contents
 stage.append(name)
focus=['assets/characters/Character1Fresh.glb','gait_motor.gd','orbit_locomotion.gd','weapon_orbit.gd',
        'field_carry.gd','field_inventory.gd','field_opening.tscn','assets/field_pack/carry_frame.glb','assets/field_pack/expedition_shelf.glb']
dest={'source':rev,'scene':m['scene'],'files_verified_against_git_and_sha256_manifest':len(stage),
      'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'key_files':{k:m['files'][k] for k in focus},
      'engine':subprocess.check_output(['godot','--version'],text=True).strip(),
      'method':'Every working byte was checked against the shipping manifest and the Git object at this revision; the source tree stores the recovered furnace in ordered pieces.'}
destination.write_text(json.dumps(dest,indent=2)+'\n')
print(rev,len(stage))
