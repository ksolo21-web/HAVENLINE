"""Discard consumed native MovieWriter scratch blocks while the independent live encoder runs."""
import sys,time,os,ctypes,pathlib
p=pathlib.Path(sys.argv[1]); libc=ctypes.CDLL(None,use_errno=True)
chunk=2*1024**2
prev=4096
for _ in range(1800):
 if p.is_file():break
 time.sleep(.1)
fd=os.open(p,os.O_RDWR)
try:
 while not (p.parent/'encoder-finished').exists():
  length=os.fstat(fd).st_size
  safe=max(4096,(length-chunk)//chunk*chunk)
  if safe>prev:
   if libc.fallocate(fd,3,ctypes.c_longlong(prev),ctypes.c_longlong(safe-prev))!=0:raise OSError(ctypes.get_errno(),os.strerror(ctypes.get_errno()))
   prev=safe
  time.sleep(.1)
finally:os.close(fd)
