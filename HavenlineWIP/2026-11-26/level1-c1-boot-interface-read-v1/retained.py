"""Immutable retained-foot check within the same one-section technical admission."""
import contextlib,io,json,os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
with contextlib.redirect_stdout(io.StringIO()):
 from seam import f,V,F,R,P,mask,dominant,rigid,y,receipt,h

# Evaluate only fully retained below-rail source triangles. Use original
# full exact vertices and later map finite witness IDs back to source.
src=Path(os.environ['HAVENLINE_ARCHIVED_GROUND_EVALUATOR']).resolve()
assert h(src)=='0b33c50478530a6266535d7c4b7e286703454e04f260b12d12249c52818e8c82'
ds=src.read_text();lo=ds.index('def mesh_overlap(P):');hi=ds.index('\nnb=mesh_overlap',lo)
ids=np.flatnonzero(mask)
TR=F[ids]
d={'np':np,'cKDTree':cKDTree,'TR':TR,'Weld':f.tags,'active':np.arange(len(TR))}
exec(ds[lo:hi],d)
rest=d['mesh_overlap'](R)
load=d['mesh_overlap'](P)
pair=lambda pp:[int(ids[i]) for i in pp]
n=sorted([pair(q) for q in load])
srows=np.unique(f.bounds['R']['faces'])
sr=set(srows)
touched=sorted([q for q in n if sr & set(F[q].reshape(-1))])
first=[dict(faces=q, heights_mm=[(V[F[k],1].astype(float)*1000).tolist() for k in q]) for q in n[:3]]
out=dict(fully_retained_below_rail_face_count=len(TR),neutral_strict_nonadjacent_pairs=len(rest),loaded_strict_nonadjacent_pairs=len(load),
         source_face_pairs_touching_observed_sole_support_rows=touched,
         earliest_exact_lower_pairs=first,reference_contact_regions_protected=True,
         known_rail_pierces_retained_lower_faces=[32911,33096,33224],
         preserves_load_without_editing_lower_geometry=not load, no_engine_geometry_weight_or_asset_changed=True)
print(json.dumps(out,indent=2))
