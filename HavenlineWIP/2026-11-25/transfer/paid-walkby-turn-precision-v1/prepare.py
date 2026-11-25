from pathlib import Path
import subprocess,sys,hashlib
p=Path(__file__).resolve().parent
original=p.parent/'hvn-l1-paid-storage-walkby-v1'
for f,h in [('probe.gd','d167a3fe37ac680a5cf82b023c8cf6677ec5956b1ccba4f52bef957b9878f436'),('SHA256SUMS','ac4a8d52a510abd6b657872fc6f73f45d043115152ce943576c365b0d4cccd80')]:
 assert hashlib.sha256((original/f).read_bytes()).hexdigest().startswith(h)
subprocess.run(['sha256sum','-c','--status','SHA256SUMS'],cwd=original,check=True)
dest=Path(sys.argv[2])
subprocess.run([sys.executable,str(original/'prepare.py'),sys.argv[1],str(dest)],check=True)
old=dest.read_text()
assert old==(original/'probe.gd').read_text()
at='func tick(n:int) -> void:'
where='\t\tprevious=curr\n'
assert old.count(at)==old.count(where)==1
addition='\t\tif tick_count in [1305,1306,1307,1352,1353,1354]:\n\t\t\tcapture_turn(carrying,curr,ds)\n'
new=old.replace(at,(p/'observer.gdfrag').read_text()+at).replace(where,addition+where)
assert new.replace((p/'observer.gdfrag').read_text(),'').replace(addition,'')==old
dest.write_text(new)
