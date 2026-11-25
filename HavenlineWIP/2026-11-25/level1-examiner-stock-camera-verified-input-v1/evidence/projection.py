"""Full-resolution exact geometry, not raster segmentation."""
from pathlib import Path
import json,struct,sys,tempfile,numpy as np
from pose_asset import bake_factory
m=Path(sys.argv[1]); data=json.loads(m.read_bytes())
bake=bake_factory(sys.argv[2],data,m)
records=[]
with tempfile.TemporaryDirectory(dir=Path.cwd(),prefix='own-projection.') as t:
 for row in data['frames']:
  if row['age_tick'] not in (0,40,100,266):continue
  p=Path(t)/'hero.glb'; bake(row,p); b=p.read_bytes(); p.unlink()
  n=struct.unpack_from('<I',b,12)[0]; d=json.loads(b[20:20+n]); count=d['accessors'][0]['count']
  points=np.frombuffer(b,'<f4',offset=n+28,count=count*3).reshape(-1,3)
  o,right,up,back=np.array(row['camera']); y=(points-o)@up*720/13; x=(points-o)@right*720/13
  records.append(dict(age=row['age_tick'],height_px=float(np.ptp(y)),width_px=float(np.ptp(x)),bounds_px=[640+x.min(),360-y.max(),640+x.max(),360-y.min()]))
print(json.dumps(dict(geometry_not_raster=True,default_uncropped_1280x720=records),indent=2))
