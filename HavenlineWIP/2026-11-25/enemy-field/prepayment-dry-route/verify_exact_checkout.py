from pathlib import Path
import hashlib, sys
here=Path(__file__).resolve().parent
root=Path(sys.argv[1])
rows=(here/'BASE-TREE.txt').read_text().splitlines()
tracked=[]
for r in rows:
 meta,name=r.split('\t')
 mode,kind,h=meta.split()
 assert kind=='blob' and mode in ('100644','100755')
 p=root/name
 assert p.is_file() and not p.is_symlink()
 d=p.read_bytes()
 assert hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()==h,name
 tracked.append(name)
x=root/'HavenlineLevel1/tests/test_prepayment_field.gd'
assert x.read_bytes()==(here/x.name).read_bytes()
print('tracked_git_blobs',len(tracked),'private_fixture',1)
