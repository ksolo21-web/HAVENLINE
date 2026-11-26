import json,subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
p=json.loads((here/'launch-contract.json').read_text())
repo=here.parent/'hvn-pad-mount-admission/isolated-source'
def git(*a):return subprocess.check_output(['git','-C',str(repo),*a]).decode().strip()
ref=p['authoritative_review_revision'];root=p['project_relative_path'];scene=p['run_scene'].removeprefix('res://')
assert git('rev-parse',ref+':'+root)==p['review_subtree']
for f,key in [('project.godot','project_blob'),(p['hydrate_from_project'],'hydrate_blob'),(scene,'scene_blob'),(scene.replace('.tscn','.gd'),'scene_script_blob')]:
 assert git('rev-parse',f'{ref}:{root}/{f}')==p[key]
g=git('show',f'{ref}:{root}/project.godot')
assert 'run/main_scene="res://opening.tscn"' in g
assert 'res://previews/integrated_opening.gd' in git('show',f'{ref}:{root}/{scene}')
assert p['generated_furnace_sha256'] in git('show',f'{ref}:{root}/{p["hydrate_from_project"]}')
print('Exact canonical integrated opening contract verified, no hydration/engine/build invocation.')
