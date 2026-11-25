"""Read-only tracked model metadata and supplied reference pixel samples."""
import hashlib,json,struct,subprocess,sys,statistics
from pathlib import Path
from PIL import Image
repo,ref=Path(sys.argv[1]),Path(sys.argv[2])
pin='11c14a1c41971067c7dc97db69375f720a408f68'
files=('HavenlineGodot/assets/environment_v2/storage.glb','HavenlineGodot/assets/world/storage.glb','HavenlineGodot/assets/stations_v2/cargo_crate.glb','HavenlineGodot/assets/stations_v2/pad_stock.glb','HavenlineLevel1/assets/studio/purchase_pad_v5.glb')
def git(*args):return subprocess.check_output(['git','-C',repo,*args])
models={}
for name in files:
 b=git('show',pin+':'+name)
 n,tag=struct.unpack_from('<II',b,12);assert tag==0x4e4f534a
 m=json.loads(b[20:20+n])
 models[name]={'blob':git('rev-parse',pin+':'+name).decode().strip(),'nodes':[x.get('name') for x in m.get('nodes',[])],'materials':[x.get('name') for x in m.get('materials',[])],'texture_count':len(m.get('textures',[]))}
samples={
 'B-008.00.png':('8544aee9feba9bdb5d3060ec8449bd2ba07f7ad4092c70599979120e3d09c65b',{'dark_field':(375,650),'gold_cut_end':(419,657),'brown_bark':(417,632),'outside_work_floor':(478,741)}),
 'B-010.00.png':('10e434c1b949d18f76e9a510c8376895e4996413d7f8ae1b2f3df924aa848e8c',{'dark_field':(610,859),'gold_cut_end':(649,859),'brown_bark':(646,831),'outside_work_floor':(710,942)})
}
report={}
for filename,(sha,points) in samples.items():
 p=ref/filename;assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
 im=Image.open(p).convert('RGB'); assert im.size==(1080,2520)
 report[filename]={'sha256':sha,'samples':{}}
 for key,(x,y) in points.items():
  region=[im.getpixel((i,j)) for i in range(x-2,x+3) for j in range(y-2,y+3)]
  report[filename]['samples'][key]={'xy':[x,y],'median_rgb':[statistics.median(ch) for ch in zip(*region)]}
print(json.dumps({'models_metadata':models,'visual_raster_swatches_not_albedo':report},indent=2))
