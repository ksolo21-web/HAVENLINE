from pathlib import Path
import os,hashlib
p=Path.cwd()/'hvn-l1-c1-rear-pose-corrective-hold-v1'
assert hashlib.sha256((p/'SHA256SUMS').read_bytes()).hexdigest()=='3f68050e897f1bcae4288898bac7e7c64d467f3101fed9efbc8fe7cfdb7299be'
for line in (p/'SHA256SUMS').read_text().splitlines():
    h, f=line.split(maxsplit=1);assert hashlib.sha256((p/f).read_bytes()).hexdigest()==h
s=(p/'audit.py').read_text().split('# Precisely separate analytic operator audit')[0]
c={'__file__':str(p/'audit.py')}
exec(compile(s,str(p/'audit.py'),'exec'),c)
np=c['np']; T=c['T']; x=[27920,28093,28305,42401]; w=np.load(p/'editable_native_pair_witness.npz')
assert np.array_equal(c['held'][T[[27920,42401]]],w['native_0ms_pair_triangles_m'])
np.savez(Path(os.environ['HVN_NEW_WITNESS'])/'exact_native_four_faces.npz',ids=x,vertices=T[x],bind=c['neutral'][T[x]],held=c['held'][T[x]])
np.savez(Path(os.environ['HVN_NEW_WITNESS'])/'exact_native_shell.npz',faces=T,bind=c['neutral'],held=c['held'],region=sorted(c['region']))
