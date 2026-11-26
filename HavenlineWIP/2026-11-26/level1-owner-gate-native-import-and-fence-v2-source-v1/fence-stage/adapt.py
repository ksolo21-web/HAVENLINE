from collections import Counter
import hashlib,json,sys
from pathlib import Path
a,b=map(Path,sys.argv[1:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p):
    files=list(p.rglob('*')); assert not any(x.is_symlink() for x in files)
    return {str(x.relative_to(p)): h(x) for x in files if x.is_file()}
prefix='previews/reference_panel/'
donor=prefix+'assets/FenceOwner33036V2'
assert h(b/(donor+'.obj'))=='694840c150cbf9150f9e66c5354a7048f3ad23d882913f7d11e6073abc24cdd0'
assert h(b/(donor+'.mtl'))=='221be7e4d2c59a3acd8da4ef48c5525f6b857a61f17a844b988ad11e11cd6c8b'
sections=[]; verts=[]
for line in (b/(donor+'.obj')).read_text().splitlines():
    fields=line.split()
    if not fields: continue
    if fields[0]=='usemtl': sections.append([fields[1],0])
    if fields[0]=='f': assert len(fields)==4; sections[-1][1]+=1
    if fields[0]=='v': verts.append(tuple(map(float,fields[1:])))
assert sections==[['amber_logs',1344],['soft_snow',1536],['front_rounded_rails',384],['ivory_hemp_warm',4320],['ivory_hemp_cream',4320]]
lo,hi=tuple(map(min,zip(*verts))),tuple(map(max,zip(*verts)))
assert lo==(-1.46603865,0.0,-.0785) and hi==(1.467039531,1.465,.066926527)
shared=[
 ('assets/Fence18595V2.obj','assets/FenceOwner33036V2.obj'),
 ('"amber_timber","draped_snow","warm_hemp","cream_hemp"','"amber_logs","soft_snow","front_rounded_rails","ivory_hemp_warm","ivory_hemp_cream"'),
 ('[1800,1920,2560,2560]','[1344,1536,384,4320,4320]'),
 ('Color(.79,.43,.225,1),Color(.88,.935,.995,1),Color(.77,.55,.32,1),Color(.91,.72,.45,1)',
  'Color(.81,.43,.17,1),Color(.94,.956,.99,1),Color(.69,.34,.15,1),Color(.91,.73,.46,1),Color(.97,.83,.56,1)')]
def change(file, pairs):
    p=b/file
    s=p.read_text()
    for old,new in pairs:
        assert s.count(old)==1,(file,old,s.count(old))
        s=s.replace(old,new)
    p.write_text(s)
func='''
# Numeric signed donor bounds (metres) and containment inside baseline art.
func _detail_bounds(detail: AABB, stock: AABB) -> bool:
	var lo := Vector3(-1.46603865,0.,-.0785)
	var hi := Vector3(1.467039531,1.465,.066926527)
	var e := .00001
	return detail.position.distance_to(lo)<e and detail.end.distance_to(hi)<e \\
		and detail.position.x>=stock.position.x-e and detail.position.y>=stock.position.y-e and detail.position.z>=stock.position.z-e \\
		and detail.end.x<=stock.end.x+e and detail.end.y<=stock.end.y+e and detail.end.z<=stock.end.z+e
'''
mount=prefix+'reference_panel.gd'
observer='tests/hvn_l1_combined_draw.gd'
change(mount,shared+[
 ('not DETAIL.get_aabb().is_equal_approx(stock.mesh.get_aabb())','not _detail_bounds(DETAIL.get_aabb(),stock.mesh.get_aabb())'),
 ('not first.basis.x.normalized().is_equal_approx(Vector3.RIGHT):','not first.basis.x.normalized().is_equal_approx(Vector3.RIGHT) or not first.basis.z.normalized().is_equal_approx(Vector3.BACK):'),
 ('REFERENCE_PANEL_V2_MATERIALS','REFERENCE_PANEL_OWNER33036_V2_MATERIALS'),
 ('\treturn ""\n','\treturn ""\n'+func)])
change(observer,shared+[
 ('"tris":16584','"tris":19648'),
 ('if not view.mesh.get_aabb().is_equal_approx(batch.multimesh.mesh.get_aabb()):','if not view.transform.basis.z.normalized().is_equal_approx(Vector3.BACK) or not _detail_bounds(view.mesh.get_aabb(),batch.multimesh.mesh.get_aabb()):'),
 ('detail.get_surface_count()!=4','detail.get_surface_count()!=5'),
 ('for i in range(4):\n\t\tvar mat','for i in range(5):\n\t\tvar mat'),
 ('var bounds := panel.mesh.get_aabb()', '''var bounds := panel.mesh.get_aabb()
	var outward := panel.global_basis.z.normalized()
	var front_dot := outward.dot(game.camera.global_basis.z.normalized())
	if not outward.is_equal_approx(Vector3.BACK) or front_dot<.64 or front_dot>.66:
		draw_failures += 1
		print("DRAW_REJECT unexpected-owner-panel-facing ",phase)
		return'''),
 ('"stock_neighbors":11','"stock_neighbors":11,"front_camera_dot":front_dot'),
 ('\treturn true\n'+'' if False else '\treturn true\n', '\treturn true\n'+func)])
old,new=map(inventory,(a,b))
assert len(old)==len(new)==141
assert set(old)-set(new)=={prefix+'assets/Fence18595V2.obj',prefix+'assets/Fence18595V3.mtl'}
assert set(new)-set(old)=={donor+'.obj',donor+'.mtl'}
assert {k for k in old.keys() & new.keys() if old[k]!=new[k]}=={mount,observer}
print(json.dumps({'equal_prior_files':137,'replacement_files':[donor+'.obj',donor+'.mtl'],
 'changed_guard_files':[mount,observer], 'triangle_sections':sections,'min':lo,'max':hi,'scene_and_gameplay_unchanged':True,'scope':'one fence module outside +Z; existing camera fixed oblique, rear not available','not_runtime_evidence':True},indent=2))
