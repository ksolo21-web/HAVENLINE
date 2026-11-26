from pathlib import Path
import sys
exec(Path('/tmp/winter-independent/gallery.py').read_text().split("for clip in ([None]")[0])
report={}
for clip in g['animations']:
 name=clip['name'];ts,mats=pose(clip);rows=np.load('/workspace/scratch/hem95-v3/eval/'+name+'.npy',mmap_mode='r')
 maxima=[float(np.abs(get_pose(m)-row).max()) for m,row in zip(mats,rows)]
 report[name]={'vertices_per_pose':len(P),'generated_pose_count':len(mats),'comparison_pose_count':len(rows),'max_component_error_m':max(maxima)}
(out/'Independent-bake.json').write_text(json.dumps(report,indent=2))
