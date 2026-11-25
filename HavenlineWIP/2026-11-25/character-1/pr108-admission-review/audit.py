"""Source-bound PR108 tool-axis check; arbitrary anchors are analytic controls, not observed game poses."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re

p = argparse.ArgumentParser()
p.add_argument('kit', type=Path)
p.add_argument('sockets', type=Path)
args = p.parse_args()
def pinned(p, expected):
    b = p.read_bytes()
    assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest() == expected
    return b.decode()
kit = pinned(args.kit, 'e36c676137882ac5d3e195645b78e30ab6c476fd')
sockets = json.loads(pinned(args.sockets, 'e075b7bb6cb824a853e3b81b4bdadd6fc9f886bb'))
assert re.search(r'tool\.global_position = hands_mid - axis \* grip_mid \* scale \+ side \* 0\.08', kit)
assert re.search(r'var scale := 0\.95 / 0\.70', kit)
assert re.search(r'var side := axis\.cross\(Vector3\.FORWARD\)', kit)
assert re.search(r'side = axis\.cross\(Vector3\.RIGHT\)', kit)
assert re.search(r'return Basis\(x_axis, y_axis\.normalized\(\), z_axis\)', kit)
assert 'attachment.position = local' in kit
assert 'attachment.override_pose' not in kit
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def mul(a,k):return [x*k for x in a]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def unit(a):return mul(a,1/norm(a))
def radial(p, org, axis):
    v=sub(p,org)
    return norm(sub(v,mul(axis,dot(v,axis))))
out={}
for tool,n in [('axe','axe_grip_y'),('pickaxe','pick_grip_y')]:
    lo,hi=sockets[n];scale=.95/.70;mid=(lo+hi)/2
    cases=[]
    for lower,upper in [([.2,0,-.4],[.2,.3,-.4]),([1,2,3],[1.2,2.88,3.3]),([-.1,2,.3],[-.1,2,-.1])]:
        axis=unit(sub(upper,lower))
        side=cross(axis,[0,0,-1])
        if norm(side)<.001: side=cross(axis,[1,0,0])
        side=unit(side)
        hm=mul([x+y for x,y in zip(lower,upper)],.5)
        center=sub(sub(hm,mul(axis,mid*scale)),mul(side,-.08))
        both=[radial(x,center,axis) for x in [lower,upper]]
        assert all(abs(x-.08)<1e-12 for x in both)
        no_offset=sub(hm,mul(axis,mid*scale))
        assert all(radial(x,no_offset,axis)<1e-12 for x in [lower,upper])
        # Even with no lateral offset, contact to these two specific grip coordinates
        # needs the current hand spread to equal the scaled axial spacing.
        cases.append({'anchor_span_m':norm(sub(upper,lower)),'radial_m':both,'axial_endpoint_mismatch_each_m':abs(norm(sub(upper,lower))-(hi-lo)*scale)/2})
    out[tool]={'fixed_grip_span_m':(hi-lo)*scale,'controls':cases}
print(json.dumps({'source':'PR108 exact kit and sockets Git blobs, world-axis algebra only','palm_offsets_serialized_norm_m':{x:norm(sockets[x]) for x in ['left_palm_local','right_palm_local','sheath_local']},'nominal_tool_axes':out},indent=2))
