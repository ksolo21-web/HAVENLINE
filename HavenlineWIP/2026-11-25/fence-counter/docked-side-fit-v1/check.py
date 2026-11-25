from pathlib import Path
import hashlib,re,runpy,contextlib,io
b=Path(__file__).resolve().parent
prior=b.parent/'havenline-l1-docked-counter-donor-v1'
s=(b/'north_counter_donor.tscn').read_text(); old=(prior/'north_counter_donor.tscn').read_text()
assert s[s.index('[node name="JoinedBarrier"'):]==old[old.index('[node name="JoinedBarrier"'):]
assert (b/'service_counter.glb').read_bytes()==(prior/'service_counter.glb').read_bytes()
assert s.count('type="CollisionShape3D"')==3 and s.count('type="BoxMesh"')==1
assert 'Color(0.3647059, 0.3176471, 0.2823529, 1)' in s and 'roughness = 0.94' in s
for f,h in [('gate_post.obj','0ed633e1bf66d6325602c60b90e8208398cc4ca0'),('boundary_v2.mtl','d64f102a78d40635222b7fc436435e3de94f99f3')]:
    data=(b/f).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==h
with contextlib.redirect_stdout(io.StringIO()):
    pts=runpy.run_path(str(prior/'check.py'))['points']
donor=min(p[0] for p in pts), max(p[0] for p in pts)
post=(b/'gate_post.obj').read_text().splitlines()
v=[tuple(map(float,line.split()[1:4])) for line in post if line.startswith('v ')]
edges=[]
mat=''
for line in post:
    if line.startswith('usemtl '): mat=line.split()[1]
    if line.startswith('f ') and mat=='timber':
        ix=[int(x.split('/')[0])-1 for x in line.split()[1:]]
        edges.extend((v[a],v[c]) for a,c in zip(ix,ix[1:]+ix[:1]))
ys=[0,.95]+[p[1] for e in edges for p in e if 0<p[1]<.95]
def width(y):
    hits=[]
    for a,c in edges:
        if min(a[1],c[1])<=y<=max(a[1],c[1]):
            if a[1]==c[1]:hits.extend([a[0],c[0]])
            else:hits.append(a[0]+(c[0]-a[0])*(y-a[1])/(c[1]-a[1]))
    return min(hits),max(hits)
for side,flank,d in [('Left',-1.825,donor[0]),('Right',1.825,donor[1])]:
    center=float(re.search(r'name="'+side+r'ArchiveTimberCap"[^\n]*\nposition = Vector3\(([^,]*),',s)[1])
    widths=[width(y) for y in ys]
    overlap=min(min(flank,d)-(center+lo) for lo,hi in widths),min(center+hi-max(flank,d) for lo,hi in widths)
    assert min(overlap)>.007
    print(side,'gap',round(abs(flank-d),6),'timber X extent overlap at sampled section sides',*(round(x,6) for x in overlap))
print('exact donor/collider+markers unchanged; no new physics for art')
