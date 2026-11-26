"""Unpack supplied Linux release to a private directory and test via its shipped launcher."""
import subprocess as sp,os,sys,ctypes as ct,re,time,pathlib as P,json,hashlib,tarfile,tempfile,shutil,math
from PIL import Image,ImageStat
app=P.Path(sys.argv[1]).resolve(); out=P.Path(sys.argv[2]).resolve();out.mkdir(exist_ok=True,parents=True)
base=P.Path(tempfile.mkdtemp(prefix='havenline-final-native-',dir='/tmp'))
env=os.environ.copy();env.update(XDG_DATA_HOME=str(base/'data'),XDG_CACHE_HOME=str(base/'cache'),XDG_CONFIG_HOME=str(base/'config'),LP_NUM_THREADS='1')
exec((P.Path(__file__).resolve().parent/'close-audit.py').read_text().split('e=os.environ.copy()')[0])
with tarfile.open(app) as t:t.extractall(base,filter='data')
launcher=next(base.glob('*.sh'))
x.XSetInputFocus.argtypes=[ct.c_void_p,ct.c_ulong,ct.c_int,ct.c_ulong];x.XKeysymToKeycode.argtypes=[ct.c_void_p,ct.c_ulong];x.XKeysymToKeycode.restype=ct.c_uint
xt=ct.CDLL('libXtst.so.6');xt.XTestFakeKeyEvent.argtypes=[ct.c_void_p,ct.c_uint,ct.c_int,ct.c_ulong]
l=base/'window.log'
with l.open('w') as log:
 p=sp.Popen([str(launcher),'--verbose','--rendering-method','gl_compatibility','--audio-driver','Dummy','--windowed','--resolution','704x396','--max-fps','24'],stdout=log,stderr=sp.STDOUT,env=env)
 start=time.monotonic();win=None
 try:
  while time.monotonic()-start<240:
   assert p.poll() is None
   for candidate in re.findall(r'^\s*(0x[0-9a-f]+) "[^"]*Havenline[^"]*"',sp.check_output(['xwininfo','-root','-tree'],text=True),re.M|re.I):
    wp=sp.check_output(['xprop','-id',candidate,'_NET_WM_PID'],text=True)
    if re.search('= '+str(p.pid)+r'(?:$|\s)',wp):win=candidate;break
   if win:
    im=out/'Packaged-start.jpg';sp.run(['import','-window',win,str(im)],check=True,timeout=10)
    pixels=list(Image.open(im).convert('RGB').resize((100,60)).get_flattened_data());light=sum(min(v)>145 for v in pixels)/len(pixels)
    if .2<light<.94:break
   time.sleep(.25)
  assert win and .2<light<.94
  d=x.XOpenDisplay(os.environ['DISPLAY'].encode());w=int(win,16);x.XSetInputFocus(d,w,1,0);x.XFlush(d)
  code=x.XKeysymToKeycode(d,ord('d'));xt.XTestFakeKeyEvent(d,code,1,0);x.XFlush(d);time.sleep(10);xt.XTestFakeKeyEvent(d,code,0,0);x.XFlush(d);time.sleep(.8)
  im2=out/'Packaged-after-movement.jpg';sp.run(['import','-window',win,str(im2)],check=True,timeout=10)
  close=time.monotonic();wmclose(w);rc=p.wait(timeout=180);closed=time.monotonic()-close
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=35)
savefiles=list((base/'data').rglob('field-inventory-v1.json'));assert len(savefiles)==1
envelope=json.loads(savefiles[0].read_text())
assert hashlib.sha256(envelope["payload"].encode()).hexdigest()==envelope["sha256"]
saved=json.loads(envelope["payload"])
def find_player(data):
 if isinstance(data,dict):
  if 'player' in data and 'x' in data['player']:return data['player']
  for v in data.values():
   r=find_player(v)
   if r:return r
 return None
player=find_player(saved);assert player
moved=math.dist((0,6),(player['x'],player['z']))
report={'launcher':launcher.name,'input':'Focus game window, hold physical D key for ten wall seconds through XTest on an isolated Xorg display, release, wait, then send WM_DELETE_WINDOW.','exit':rc,'distance_from_spawn_m':moved,'saved_player':player,'close_to_exit_s':round(closed,3),'profile_path_inside_private_XDG':str(savefiles[0].relative_to(base/'data')),'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [app,im,im2]},'native_resolution':list(Image.open(im).size),'warnings':[s for s in l.read_text().splitlines() if 'WARNING:' in s or 'ERROR:' in s],'leaks':[s for s in l.read_text().splitlines() if 'leaked' in s.lower()],'renderer':next(s for s in l.read_text().splitlines() if 'Using Device' in s)}
assert rc==0 and moved>.5 and not report['leaks'],report
(out/'Linux-launcher-and-movement.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.rmtree(base)
print(json.dumps(report,indent=2))
