from pathlib import Path
import hashlib,json,subprocess,sys
p='11c14a1c41971067c7dc97db69375f720a408f68'
repo=sys.argv[1]
def git(*args):return subprocess.check_output(['git','-C',repo,*args]).decode()
paths={k:git('rev-parse',p+':'+k).strip() for k in [
 'HavenlineLevel1/layout.json','HavenlineLevel1/previews/integrated_opening.gd',
 'HavenlineLevel1/resources/typed_receiver.gd','HavenlineLevel1/docs/TYPED_RECEIVER_VERIFICATION.md',
 'HavenlineGodot/scripts/storage_stockpile.gd','HavenlineGodot/scripts/main.gd',
 'HavenlineGodot/scripts/simulation.gd','HavenlineGodot/assets/environment_v2/storage.glb',
 'HavenlineGodot/assets/world/storage.glb']}
layout=json.loads(git('show',p+':HavenlineLevel1/layout.json'))
assert not any('storage' in k.lower() for k in layout)
r=Path('../hvn-l1-transfer-crown-spacing-independent-v1')
assert hashlib.sha256((r/'SHA256SUMS').read_bytes()).hexdigest()=='91777bed75993f6b841615f6f7104594cabb57056518a5be8f2a75847d903c27'
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=r,check=True)
v=json.loads((r/'results.json').read_text())
x,y,z=v['dimensions_m']; px,py,pz=v['separated_pitch_m']
fit={'single_bounds_m':v['dimensions_m'],'two_parallel_side_by_side_box_m':[x,y,z+pz],'two_parallel_end_to_end_box_m':[x+px,y,z],'type':'sufficient disjoint axis-aligned whole-bound rectangle with 1mm separation, not true minimum or stability'}
print(json.dumps({'paths':paths,'level1_storage_named_tracked_files':[x for x in git('ls-tree','-r','--name-only',p,'HavenlineLevel1').splitlines() if 'storage' in x.lower() or 'stockpile' in x.lower()],'active_typed_receiver_sites':git('grep','-n','receiver','11c14a1c','--','HavenlineLevel1/previews/integrated_opening.gd','HavenlineLevel1/opening.gd').splitlines(),'fit':fit},indent=2))
