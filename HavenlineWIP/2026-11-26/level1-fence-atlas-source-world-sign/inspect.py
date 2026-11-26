from pathlib import Path
import numpy as np,json,hashlib
from PIL import Image
R=Path(__file__).resolve().parent;P=R.parent
D=P/'hvn-l1-fence-33036-uncompressed-import-v1/import-evidence.iTjqXRVx'
E=P/'hvn-l1-fence-33036-signed-atlas-probe-v1/private-parser.zlmkHRp4/native-output.eQyKp7e9'
S=P/'hvn-l1-fence-33036-rooted-emboss-module-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def j(dirname,name,h):
 p=next(dirname.rglob(name));assert sha(p)==h
 return json.loads(p.read_text())
m=j(D,'basis.json','b251dc9038a8aa1850e23045db21564238634e1da98b9f01b4ba9bcd2e06cda5')
r=j(E,'signed-atlas.json','6d1770599f4ef02309953ba45f548ec735d2e3c1136246aa919d6447da40343e')
assert r['actual_texture_runtime_bytes_match']
t=m['surfaces'][0]['corners'][60:63]
p=np.array([v[:3] for v in t]);uv=np.array([v[3:5] for v in t]); ns=np.array([v[5:8] for v in t]); ts=np.array([v[8] for v in t])
A,B=p[1:]-p[0]; v=uv.copy();v[:,1]=1-v[:,1]
a,b=v[1:]-v[0]
norm=lambda x:x/np.linalg.norm(x)
dA,dB=(A*b[1]-B*a[1])/(a[0]*b[1]-a[1]*b[0]),(-A*b[0]+B*a[0])/(a[0]*b[1]-a[1]*b[0])
normal=norm(ns.sum(0)); tan=norm(ts[:,:3].sum(0)); bit=norm(np.cross(normal,tan))*ts[0,3]
src_bit=-bit
rgb=np.array(r['center_rgb_cases'])[:,1:]
assert rgb[3,0]>rgb[1,0]>rgb[2,0] and ts[:,3].tolist()==[-1.]*3
assert norm(dA)@tan>.95 and norm(dB)@bit<-.8
im=S/'RopeFiberNormal.png'; assert sha(im)=='c6e1c6fed3f84e4bec559b39d2ccb1df21f61c290d15d7f532f42e584ef308c9'
g=np.asarray(Image.open(im))[:,:,1]
s={'status':'source convention established; correction plan only, no pixels changed',
 'actual_triangle_native_uv':uv.tolist(),
 'native_tangent_X_world':tan.tolist(),'original_increasing_V_world':norm(dB).tolist(),'native_positive_green_B_world':bit.tolist(),'positive_source_chart_b_orthonormal_world':src_bit.tolist(),
 'native_plus_green_alignment_vs_original_increasing_V':float(norm(dB)@bit),'native_tangent_alignment_vs_original_increasing_U':float(norm(dA)@tan),
 'native_controls_center_red_rgb8':[int(round(255*x)) for x in rgb[:,0]],'original_green_min_max':[int(g.min()),int(g.max())],
 'plan':'Apply one generation-level green reflection on a detached copy, approximation by raw RGB8 Gprime=255-G only. Do not reverse rows or flip UV or change native tangent w or decode sRGB, and retain R/B byte identity. Test known green signs and corrected original patch if separately authorized.'}
print(json.dumps(s,indent=2))
