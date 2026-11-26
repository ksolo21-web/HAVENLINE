from collections import Counter
from pathlib import Path
import hashlib,json,re,sys
root=Path(sys.argv[1])
p=root/'candidate/Fence18595V2.obj'
m=root/'candidate/Fence18595V2.mtl'
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(p)=='137446d82b7c679c88f85069958b0eaacb85ca38dc8d1e7f73be5bef89b7ec53'
assert sha(m)=='c606aaf113f042e22146e199f7308d9b604e5075ba62b5b8a27ffb139ecbc3f0'
seq=[]; groups=[]; counts=Counter()
for l in p.read_text().splitlines():
    w=l.split()
    if not w:continue
    if w[0]=='o': groups.append(w[1:])
    if w[0]=='g': raise AssertionError('unexpected OBJ group')
    if w[0]=='usemtl': seq.append(w[1])
    if w[0]=='f': counts[seq[-1]]+=len(w)-3
assert groups==[['Fence18595V2']]
assert seq==['amber_timber','draped_snow','warm_hemp','cream_hemp']
assert [counts[s] for s in seq]==[1800,1920,2560,2560] and counts.total()==8840
assert sorted(re.findall(r'^newmtl (.*)$',m.read_text(),re.M))==sorted(seq)
assert not re.search(r'^\s*(map_\w+|Ka|bump|disp|decal)\s',m.read_text(),re.M)
print(json.dumps({'obj_sha256':sha(p),'mtl_sha256':sha(m),'ordinal_source_face_stream':[{'name':s,'triangle_count':counts[s]} for s in seq],
    'four_single_contiguous_source_segments_not_native_assumption':True,'texture_maps_ka_or_optional_paint':False},indent=2))
