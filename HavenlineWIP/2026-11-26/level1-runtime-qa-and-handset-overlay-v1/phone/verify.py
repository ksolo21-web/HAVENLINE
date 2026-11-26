from pathlib import Path
from hashlib import sha256
from configparser import ConfigParser
import json,re,subprocess,shutil
here=Path(__file__).resolve().parent
root=here.parent
repo=root/'hvn-pad-mount-admission/isolated-source'
ref='11c14a1c41971067c7dc97db69375f720a408f68'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def get(rel):return git('show',ref+':'+rel)
assert git('rev-parse',ref+'^{tree}').decode().strip()=='e9c03d776f5826570a02a1b6b04da68743ee59fe'
assert git('rev-parse',ref+':HavenlineLevel1').decode().strip()=='d764a05246cbff96983aa27af17e2e919a946ae0'
entries=git('ls-tree','-r','--name-only',ref,'HavenlineLevel1').decode().splitlines()
assert len(entries)==126 and 'HavenlineLevel1/export_presets.cfg' not in entries
prov=root/'hvn-l1-handset-export-provenance-v1'
assert sha256((prov/'SHA256SUMS').read_bytes()).hexdigest()=='f5ce9a5284f294eba3cfb623a94a2df006960852ea0dc3a51e23871e007a4dcf'
for line in (prov/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);assert sha256((prov/n).read_bytes()).hexdigest()==h
original=get('HavenlineLevel1/project.godot')
stage=here/'overlay'; replacement=(stage/'project.godot').read_bytes()
old=b'run/main_scene="res://opening.tscn"'
new=b'run/main_scene="res://previews/integrated_opening.tscn"'
assert original.count(old)==1 and replacement==original.replace(old,new)
assert sorted(x.name for x in stage.iterdir())==['export_presets.cfg','project.godot']
target='HavenlineLevel1/previews/integrated_opening'
assert '[node name=' in get(target+'.tscn').decode()
g=get(target+'.gd').decode()
ready=g[g.index('func _ready()'):].split('\nfunc ',1)[0]
assert 'super._ready(' not in ready and 'configure' not in ready and 'configure_session_profile' not in ready and 'save.commit' not in ready
# Actual loose runtime inputs, not debug-only doc fixtures.
assert 'res://layout.json' in g and 'res://conifers.json' in get('HavenlineLevel1/opening.gd').decode()
def cfg(raw):
 c=ConfigParser(interpolation=None);c.read_string(raw.decode());return c
c=cfg((stage/'export_presets.cfg').read_bytes())
historic=get('HavenlineGodot/export_presets.cfg')
assert git('rev-parse',ref+':HavenlineGodot/export_presets.cfg').decode().strip()=='75f6ae72de760c4ae127d4827c83e53330ccca84'
assert git('rev-parse',ref+':.github/workflows/havenline-godot-android.yml').decode().strip()=='6bc0ed7662b47dfbbe12606731e1e39e9413b2b4'
p=c['preset.0'];o=c['preset.0.options'];old_o=cfg(historic)['preset.0.options']
assert c.sections()==['preset.0','preset.0.options']
assert set(o)<=set(old_o) and set(p)<=set(cfg(historic)['preset.0'])
assert p['platform']=='"Android"' and p['export_filter']=='"all_resources"' and p['export_path']=='""'
assert set(p['include_filter'].strip('"').split(','))=={'layout.json','conifers.json'}
assert {k:v for k,v in o.items() if k.startswith('architectures/')}=={'architectures/armeabi-v7a':'false','architectures/arm64-v8a':'true','architectures/x86':'false','architectures/x86_64':'false'}
assert o['package/unique_name']=='"com.havenline.qa.l1r11c14a"' and o['package/unique_name']!=old_o['package/unique_name']
assert not any('keystore' in k for k in o)
assert o['package/retain_data_on_uninstall']==o['user_data_backup/allow']=='false'
permissions={k:v for k,v in o.items() if k.startswith('permissions/')}
assert permissions=={k:'false' for k in ('permissions/internet','permissions/record_audio','permissions/read_external_storage','permissions/write_external_storage')}
print(json.dumps({'verdict':'SOURCE-READY / EXPORT HOLD','ref':ref,'source_paths':len(entries),'overlay_delta':['integrated opening main-scene key only','separate one-entry ARM64 review preset'],'manifest_permissions_not_yet_verified':True,'tool_inventory_only':{n:bool(shutil.which(n)) for n in ('adb','apksigner','java')},'binary_or_device':False,'durability':'ephemeral only'},indent=2))
