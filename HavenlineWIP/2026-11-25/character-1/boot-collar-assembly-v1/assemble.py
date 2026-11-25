import os
import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
prev=Path(os.environ['C1_LAYERED_DATA'])
A=np.load(prev/'exact-assembled-surface.npz')
F=np.load((Path(os.environ['C1_KNEE_DATA'])/'poses.npz'))
V=A['v'].copy(); F0=A['tri']; W=A['w']; E=A['trim_v'].copy(); E0=A['trim_f']
auth=json.loads((P/'stack.json').read_text()); C=np.array(auth['cap_origin_m']); B=np.array(auth['basis']); N=B[:,2]
half_lo=max(r['max_mm_relative_to_exact_cap'] for r in auth['nearest'] if r['max_mm_relative_to_exact_cap']<0)/1000
assert -.000208<half_lo<-.000203
# Joint split through the real available slab: half retained material section,
# half designed gap to measured facing leather. Keep original exterior exact.
well=.5*half_lo
top=E[:5].copy()
E[5:]=top+well*N
# Recess only the previously generated leather fan center; its surrounding
# original material boundary and source vertices are unmodified. Depth anchored
# to old peak gap, preserves positive shape/material topology.
old=V[-1].copy(); oldZ=(old-C)@N
assert oldZ<well
V[-1]=old-.25*abs(half_lo)*N
bpy.ops.wm.open_mainfile(filepath=str(prev/'c1-right-boot-cohesive-rest-proof.blend'))
p=bpy.data.objects['Manual upper-boot lapped trim panel rigid to right shin']
k=bpy.data.objects['Right boot visible repaired leather rest proof']
S=float(F['scale']);O=F['source_origin']
def coords(obj):return (np.array([vv.co[:] for vv in obj.data.vertices],float)-O)*S
def cs(obj):return np.array([v.vector[:] for v in obj.data.corner_normals])
n=cs(p)
old_uv=np.array([v.uv[:] for v in p.data.uv_layers.active.data])
old_uv2=np.array([v.uv[:] for v in k.data.uv_layers.active.data])
old_p=coords(p);old_k=coords(k)
k.data.vertices[-1].co=V[-1]/S+O
for j in range(5,10):p.data.vertices[j].co=E[j]/S+O
k.data.update();p.data.update()
now=cs(p)
assert np.array_equal(coords(p)[:5],old_p[:5]) and np.array_equal(coords(k)[:-1],old_k[:-1])
assert np.array_equal(np.array([v.uv[:] for v in p.data.uv_layers.active.data]),old_uv) and np.array_equal(np.array([v.uv[:] for v in k.data.uv_layers.active.data]),old_uv2)
assert np.max(abs(now[:9]-n[:9]))<=1e-6  # first three triangles are exposed cap
bpy.ops.wm.save_as_mainfile(filepath=str(P/'c1-right-boot-layered-assembly-proof.blend'),compress=True)
np.savez_compressed(P/'exact-assembled-surface.npz',v=V,tri=F0,w=W,UV=A['UV'],trim_v=E,trim_f=E0,retained_old_ids=A['retained_old_ids'],new_caps=A['new_caps'],new_lower=A['new_lower'])
q={'actual_cap_points_unmodified':True,'cap_real_corner_normals_difference':float(np.max(abs(now[:9]-n[:9]))),'retained_uv_bits_all_equal':True,'new_underside_plane_mm_relative_cap':well*1000,'measured_below_cap_max_mm':half_lo*1000,'new_recess_author_point_mm':float((V[-1]-old)@N)*1000,'identity_version_untouched':True}
(P/'assembly.json').write_text(json.dumps(q,indent=2));print(q,flush=True)
