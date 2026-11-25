#!/usr/bin/env python3
"""Pure math: same pure heading change, fixed palms; no engine execution."""
from pathlib import Path
import hashlib,json,math,sys
paths=[Path(x) for x in sys.argv[1:]]
assert len(paths)==6,"kit opening integrated sockets exact-yaw-log patched-kit"
pins=[
"6c206a92beaed7cfc585d9244f2946f5f3cecf6ada9eab5ac8f629d6e0facde7",
"5ad3f2c772ab91153d3fae798d9fd936a20288c1bd4aef3a3d9624154ace8d95",
"6dcc81d6ae17940271fbc54f2ccc2c43ab8a2cbeb2e54caf4c405a56dc6d8815",
"0ea40afc2b5ac940efbca1510d3fc4df5926c58a94ba0df5a60081debd8646e2",
"a6e774980cf53669efe07dd79d45b4d7586189b9b25f43ccf97bacc9ade78fa1"]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert [sha(p) for p in paths[:5]]==pins
old,opening,integrated,sockets,log,new=(p.read_text() for p in paths)
g=new.encode()
assert hashlib.sha1(f"blob {len(g)}\0".encode()+g).hexdigest()=="84b7ec4fd5d09e20e5422a30d2193c208bd57627"
assert "func model(resource: PackedScene, parent: Node3D, height: float)" in opening and "parent.add_child(model_root)" in opening
assert all("model(HERO, actor," in src and "character_kit.install(self, hero_visual," in src for src in (opening,integrated))
assert "_held_actor = visual.get_parent_node_3d()" in new
assert "actor_frame * Vector3.FORWARD" in new and "actor_frame * Vector3.RIGHT" in new
assert "_held_actor.global_transform.basis.orthonormalized()" in new
assert "Basis(side, axis, side.cross(axis).normalized())" in new
for x in ('if lower.y > upper.y:', 'if span.length() < 0.05:', 'side * 0.08', 'var scale := 0.95 / 0.70'):
 assert x in old and x in new
assert old[old.index('func _stick('):]==new[new.index('func _stick('):]
# Native evidence anchors one actual fixed-pose 180-degree contrast; authored GLB stays untouched.
j=json.loads(log[log.index('{'):]); s=json.loads(sockets); scale=.95/.70; side_offset=.08
F=(0.,0.,-1.); R=(1.,0.,0.); VX=(.21,1.04,.23)
from math import sqrt
def mul(a,c):return tuple(x*c for x in a)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return add(a,mul(b,-1.))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):
 x,y,z=a;u,v,w=b
 return (y*w-z*v,z*u-x*w,x*v-y*u)
def mag(v):return sqrt(dot(v,v))
def unit(v):return mul(v,1/mag(v))
def rotate(v,deg):
 x,y,z=v; a=math.radians(deg); c=math.cos(a); n=math.sin(a)
 return (c*x+n*z,y,c*z-n*x)
def rounded_frame(vs):return [[round(x,9) for x in v] for v in vs]
def make_local(axis,mid,pivot,head,use_actor,grips):
 # Rigid body yaw and translation; exact source world-Y assignment stays unchanged.
 def world(v):return add(pivot,rotate(v,head))
 def av(v):return rotate(v,-head)
 lo=world(sub(mid,mul(axis,.14)))
 hi=world(add(mid,mul(axis,.14)))
 if lo[1]>hi[1]:lo,hi=hi,lo
 a=unit(sub(hi,lo))
 ref_f=rotate(F,head) if use_actor else F
 ref_r=rotate(R,head) if use_actor else R
 x=cross(a,ref_f); branch="primary"
 if mag(x)<.001:
  x=cross(a,ref_r);branch="fallback"
 x=unit(x)
 z=unit(cross(x,a))
 assert abs(dot(x,a))<1e-12 and abs(dot(x,z))<1e-12 and dot(cross(x,a),z)>1-1e-12
 pos=add(sub(mul(add(lo,hi),.5),mul(a,sum(grips)/2*scale)),mul(x,side_offset))
 orig=av(sub(pos,pivot))
 bands=[av(sub(add(pos,mul(a,k*scale)),pivot)) for k in grips]
 return orig,av(mul(x,scale)),av(mul(a,scale)),av(mul(z,scale)),bands,branch
def ferr(a,b):return max(mag(sub(x,y)) for x,y in zip(a[:4],b[:4]))
def berr(a,b):return max(mag(sub(x,y)) for x,y in zip(a[4],b[4]))
cases={}; headings=(0,33,91,180,-147)
P=j['actor_pivot_world']; witness0=j['actor_local_heading0']; witness180=j['actor_local_heading180']
A=unit(witness0['y'])
xi=unit(witness0['x'])
M=sub(add(witness0['origin'],mul(A,sum(s['axe_grip_y'])/2*scale)),mul(xi,side_offset))
native_expected=tuple(witness180[k] for k in ('origin','x','y','z'))
base180=make_local(A,M,P,180,False,s['axe_grip_y'])
base_native_err=ferr(base180,native_expected)
assert base_native_err<3e-7 and abs(j['delta_norm_m']-.16)<1e-6
for name,axis,mid,grips,branch in (
("exact_native_axe_axis",A,M,s['axe_grip_y'],"primary"),
("exact_forward_degeneracy",F,VX,s['pick_grip_y'],"fallback"),
("near_forward_below_point001",unit((.0004,0,-1.)),VX,s['axe_grip_y'],"fallback"),
("near_forward_above_point001",unit((.0016,0,-1.)),VX,s['pick_grip_y'],"primary")):
 N=make_local(axis,mid,P,0,False,grips)
 c=[make_local(axis,mid,P,h,True,grips) for h in headings]
 assert all(k[5]==branch for k in c)
 assert max(ferr(k,N) for k in c)<1e-11 and max(berr(k,N) for k in c)<1e-11
 assert abs(mag(sub(N[0],sub(mid,mul(N[2],sum(grips)/2))))-.08)<1e-11
 B=make_local(axis,mid,P,180,False,grips)
 assert abs(mag(sub(B[0],N[0]))-.16)<1e-10
 assert mag(add(B[1],N[1]))<1e-10 and mag(add(B[3],N[3]))<1e-10
 assert mag(sub(B[2],N[2]))<1e-10
 cases[name]={"candidate_max_local_frame_error_m_or_axis":max(ferr(k,N) for k in c),
   "candidate_max_band_drift_m":max(berr(k,N) for k in c),"baseline_half_turn_origin_drift_m":mag(sub(B[0],N[0])),
   "neutral_scale":mag(c[0][2]),"held_side_branch":branch,"native_scale_changes":False}
print(json.dumps({"input_sha256":pins,"headings_deg":headings,"analytic_native_180_frame_error_m_or_axis":base_native_err,
 "cases":cases,"scope":"offline pure yaw; no hand sorting, grip, sheathed branch, runtime or visual approval"},indent=2,sort_keys=True))
