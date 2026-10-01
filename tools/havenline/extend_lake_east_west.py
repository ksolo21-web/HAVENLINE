#!/usr/bin/env python3
"""Apply the locally tested T02 lake correction, refusing any concurrent edits.
Only the basin/coast, matching materials and dry-shore recovery change.
Original models, source contract, prices, forest renderer and camera are preserved.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BEFORE={
'HavenlineGodot/scripts/outpost_surface.gd':'f2fc3b015f9e06b3dd2a2f5b0beecebd69a2627ffed2eb336e09f3ad4c0e5da3',
'HavenlineGodot/scripts/outpost_view.gd':'8b329f1f279f4d7a63c96924f231090436dcc44bcd6620f0c3ec71b4b875e746',
'HavenlineGodot/scripts/outpost_simulation.gd':'b5d59afe20edcd93b6e95ac37dcf2f7b02d94947122b3fa878eaa1a532f52c79',
'HavenlineGodot/shaders/outpost_snow.gdshader':'6c178772b867b17a5ce14445539b31bc24116039c5fe4e6a2e40c65c2e66a30c',
'HavenlineGodot/shaders/lakeshore_water.gdshader':'2da24abe9e0069d508d7ded7fbfb936301b7f01d0d2f531ea213c2dd9017ef76',
'HavenlineGodot/tests/test_task02_terrain.gd':'1dd4167c9b9aa0531a38d3afd3e372cb80b4dee7ef2117b5759b247ca86ad430'}
AFTER={
'HavenlineGodot/scripts/outpost_surface.gd':'75c92cccf39d1446d6f9cbf6262aaf92b4400ce4018226fdce307794ebf4850e',
'HavenlineGodot/scripts/outpost_view.gd':'0ab2b6be78dcf71ac11f931e15018cab175814519a063f8041d23fd423d14c55',
'HavenlineGodot/scripts/outpost_simulation.gd':'20d919d0fb1f38a92bc249722409116b14b57f943dccbcb519db2540231bb934',
'HavenlineGodot/shaders/outpost_snow.gdshader':'100b5d9ddf909f2a3c79f4458bce2face47845ddcca8518bd3fa938bf8f216bc',
'HavenlineGodot/shaders/lakeshore_water.gdshader':'ffa9ee60e87cafda8fee89d356ef88008a8de658c2997843bfcb00e8c45898e5',
'HavenlineGodot/tests/test_task02_terrain.gd':'1b891ac7cafd03f4d257e72a94136702ab97cb0a499d9fae98f6ea52e3c3b0fd'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if not all(sha(ROOT/n)==h for n,h in AFTER.items()):
 for n,h in BEFORE.items():assert sha(ROOT/n)==h,'Concurrent runtime edit: '+n
 p=ROOT/'HavenlineGodot/scripts/outpost_surface.gd';s=p.read_text().replace('Vector2(-7.6, -13.85)','Vector2(0.0, -13.85)').replace('Vector2(5.2, 1.85)','Vector2(15.2, 1.85)')
 a=s.index('static func coast_shape');b=s.index('static func _shape_height',a)
 s=s[:a]+'''static func lake_distance(p: Vector2) -> float:
	# World-unit capsule distance: consistent bank width along the full east-west
	# lake, including both rounded ends. Water continues beyond x=+/-14.2.
	var q := (p-LAKE_CENTER).abs()
	var straight_half := LAKE_HALF.x-LAKE_HALF.y
	return Vector2(maxf(q.x-straight_half,0.0),q.y).length()-LAKE_HALF.y

static func southern_shore_y(x: float, margin := LAND_MARGIN) -> float:
	var radius := LAKE_HALF.y+maxf(margin,0.0)+0.00005
	var dx := maxf(absf(x-LAKE_CENTER.x)-(LAKE_HALF.x-LAKE_HALF.y),0.0)
	return LAKE_CENTER.y+sqrt(maxf(radius*radius-dx*dx,0.0))

static func land_position(p: Vector2, margin := LAND_MARGIN) -> Vector2:
	if not p.is_finite(): return Vector2.ZERO
	# End-to-end water separates the former north strip from the active camp.
	# Recover old actors to the connected south bank, preserving X instead of
	# radially flinging them beyond the playable east/west bounds.
	var radius := LAKE_HALF.y+maxf(margin,0.0)
	var in_span := absf(p.x-LAKE_CENTER.x)<=LAKE_HALF.x+maxf(margin,0.0)
	if not in_span: return p
	var shore := southern_shore_y(p.x,margin)
	if p.y>=shore: return p
	# Only the existing playable north strip and lake need recovery; decorative
	# far-north forest geometry is not an actor destination or a terrain clamp.
	if p.y>=-16.2001 or lake_distance(p)<radius-LAKE_HALF.y:
		return Vector2(p.x,shore)
	return p

'''+s[b:]
 a=s.index('\t# Extend beyond the actual ground/water intersection');b=s.index('\tfor i in range(contour.size()):',a)
 s=s[:a]+'''	# Keep the contour buried 0.20 world units inside the physical snow bank.
	# Ninety-six samples per semicircle retain the 192-triangle water budget.
	var radius := LAKE_HALF.y+0.20
	var straight_half := LAKE_HALF.x-LAKE_HALF.y
	for side in [1.0,-1.0]:
		for i in range(96):
			var a := -PI*.5+PI*float(i)/95.0+(PI if side<0.0 else 0.0)
			contour.append(LAKE_CENTER+Vector2(side*straight_half+radius*cos(a),radius*sin(a)))
'''+s[b:];p.write_text(s)
 for name in ['HavenlineGodot/shaders/outpost_snow.gdshader','HavenlineGodot/shaders/lakeshore_water.gdshader']:
  p=ROOT/name;s=p.read_text().replace('vec2(-7.6,-13.85)','vec2(0.0,-13.85)').replace('vec2(5.2,1.85)','vec2(15.2,1.85)')
  if 'outpost_snow' in name:
   a=s.index(' vec2 signed_q=(p-lake_center)');b=s.index('\n}',a)
   s=s[:a]+''' vec2 q=abs(p-lake_center);
 return length(vec2(max(q.x-(lake_half.x-lake_half.y),0.),q.y))-lake_half.y;'''+s[b:]
  else:
   a=s.index(' vec2 p=world_xz;');b=s.index('\n float depth=',a)
   s=s[:a]+''' vec2 p=world_xz;vec2 q=abs(p-lake_center);
 float sd=length(vec2(max(q.x-(lake_half.x-lake_half.y),0.),q.y))-lake_half.y;'''+s[b:]
  p.write_text(s)
 p=ROOT/'HavenlineGodot/scripts/outpost_view.gd';s=p.read_text().replace('ground_material.shader=load("res://shaders/outpost_snow.gdshader")','ground_material.shader=load("res://shaders/outpost_snow.gdshader")\n\tground_material.set_shader_parameter("lake_center",Surface.LAKE_CENTER)\n\tground_material.set_shader_parameter("lake_half",Surface.LAKE_HALF)').replace('lake_material.shader=load("res://shaders/lakeshore_water.gdshader")','lake_material.shader=load("res://shaders/lakeshore_water.gdshader")\n\tlake_material.set_shader_parameter("lake_center",Surface.LAKE_CENTER)\n\tlake_material.set_shader_parameter("lake_half",Surface.LAKE_HALF)').replace('T02-rounded-bank-and-snow-finish','T02-east-west-end-to-end-lake').replace('"shared_actor_surface":true,','"lake_half":[Surface.LAKE_HALF.x,Surface.LAKE_HALF.y],\n\t\t"lake_extent_x":[Surface.LAKE_CENTER.x-Surface.LAKE_HALF.x,Surface.LAKE_CENTER.x+Surface.LAKE_HALF.x],\n\t\t"east_west_end_to_end":true,"shared_actor_surface":true,');p.write_text(s)
 p=ROOT/'HavenlineGodot/scripts/outpost_simulation.gd';s=p.read_text();a=s.index('\nfunc constrain_shoreline')
 s=s[:a]+'''
func _init(data: Dictionary = {}, chosen_lead: int = 1):
	super(data,chosen_lead)
	# Preserve the historical on-disk contract and all prices/progression. Resolve
	# its now-submerged future north-gate approach onto connected dry shoreline.
	contract=contract.duplicate(true)
	tuning=contract.openingLoopTuning
	var gate := Terrain.land_position(point(contract.world.forestGate),0.50)
	contract.world.forestGate=[gate.x,float(contract.world.forestGate[1]),gate.y]
'''+s[a:];p.write_text(s)
 p=ROOT/'HavenlineGodot/tests/test_task02_terrain.gd';s=p.read_text().replace('Vector2(0,-14.8),Vector2(-12,-11)','Sim.point(sim.contract.world.forestGate),Vector2(-12,-11)').replace('[Vector2(0,.2),Vector2(0,-14.8)]','[Vector2(0,.2),Sim.point(sim.contract.world.forestGate)]');p.write_text(s)
for n,h in AFTER.items():assert sha(ROOT/n)==h,'Applied source differs from local tested version: '+n
p=ROOT/'Docs/Production/task-gates.json';tracker=json.loads(p.read_text())
if tracker.get('active_status')!='REOPENED_USER_LAKE_EXTENSION':
 tracker.setdefault('historical_approvals',[]).append(tracker.get('latest_completed_task'))
 tracker.update(approved_tasks=['T01'],approved_task_count=1,active_task='T02',active_task_title='Lake extension across the full east-west playable width',active_status='REOPENED_USER_LAKE_EXTENSION',active_candidate_source=None,active_score=None,active_task_implementation_started=True,next_task='T03',next_task_locked=True)
 tracker['completed_task_records']['T02']['status']='SUPERSEDED_BY_USER_LAKE_EXTENSION_PENDING_NEW_REVIEW'
 tracker['latest_completed_task']=tracker['completed_task_records']['T01']
 tracker['checkpoint_correction']='Kaleb requested a much longer lake, end-to-end east-west. T02 is reopened; old lake approval is historical only. T03 and later remain locked. Preserve T01 assets and all original characters. Fresh tests/captures and both critic roles are required.'
 p.write_text(json.dumps(tracker,indent=2)+'\n')
print(json.dumps({'correction':'T02-east-west-lake','lake_extent_x':[-15.2,15.2],'playable_extent_x':[-14.2,14.2],'tested_runtime_hashes':AFTER,'task_approved':False,'next_task_locked':True}))
