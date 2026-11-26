import subprocess as sp,os,sys,ctypes as ct,re,time,pathlib as P,json
t=P.Path('/tmp/hl-critic-audio')
class Data(ct.Union): _fields_=[('b',ct.c_char*20),('s',ct.c_short*10),('l',ct.c_long*5)]
class Client(ct.Structure): _fields_=[('type',ct.c_int),('serial',ct.c_ulong),('send_event',ct.c_int),('display',ct.c_void_p),('window',ct.c_ulong),('message_type',ct.c_ulong),('format',ct.c_int),('data',Data)]
class Event(ct.Union): _fields_=[('message',Client),('padding',ct.c_long*24)]
x=ct.CDLL('libX11.so.6'); x.XOpenDisplay.argtypes=[ct.c_char_p];x.XOpenDisplay.restype=ct.c_void_p
x.XInternAtom.argtypes=[ct.c_void_p,ct.c_char_p,ct.c_int];x.XInternAtom.restype=ct.c_ulong
x.XSendEvent.argtypes=[ct.c_void_p,ct.c_ulong,ct.c_int,ct.c_long,ct.POINTER(Event)];x.XFlush.argtypes=[ct.c_void_p]
def wmclose(w):
 d=x.XOpenDisplay(os.environ['DISPLAY'].encode()); assert d
 event=Event(); message=event.message; message.type=33;message.send_event=1;message.display=d;message.window=w
 message.message_type=x.XInternAtom(d,b'WM_PROTOCOLS',0);message.format=32;message.data.l[0]=x.XInternAtom(d,b'WM_DELETE_WINDOW',0)
 assert x.XSendEvent(d,w,0,0,ct.byref(event))
 x.XFlush(d)
e=os.environ.copy();e.update(XDG_DATA_HOME=str(t/'wm-data'),XDG_CACHE_HOME=str(t/'wm-cache'),XDG_CONFIG_HOME=str(t/'wm-config'),LP_NUM_THREADS='1')
lines={}
for i in range(2):
 log=t/f'wm-{i}.log'
 with log.open('w') as file:
  p=sp.Popen([str(t/'Havenline-Mining.x86_64'),'--verbose','--audio-driver','Dummy','--rendering-method','gl_compatibility','--resolution','512x288','--windowed','--max-fps','20'],env=e,stdout=file,stderr=sp.STDOUT)
  start=time.monotonic();win=None
  try:
   while time.monotonic()-start<60:
    tree=sp.check_output(['xwininfo','-root','-tree'],text=True)
    for name in re.findall(r'^\s*(0x[0-9a-f]+) "[^"]*Havenline[^"]*"',tree,re.M|re.I):
     pid=sp.run(['xprop','-id',name,'_NET_WM_PID'],capture_output=True,text=True).stdout
     if re.search('= '+str(p.pid)+'(?:$|\\s)',pid):win=int(name,16);break
    if win and 'world_landscape.gd' in log.read_text() and time.monotonic()-start>4:break
    assert p.poll() is None;time.sleep(.2)
   assert win
   before=time.monotonic()
   wmclose(win)
   code=p.wait(timeout=60)
   lines['graceful_'+str(i)]={'exit_code':code,'window_close_to_exit_s':round(time.monotonic()-before,3),'renderer':next(v for v in log.read_text().splitlines() if 'Using Device' in v),'warnings':[v for v in log.read_text().splitlines() if 'WARNING:' in v or 'ERROR:' in v],'leak_instances':[v for v in log.read_text().splitlines() if 'leaked' in v.lower() or 'leaked instance' in v.lower()]}
  finally:
   if p.poll() is None:p.terminate();p.wait(timeout=30)
for i in (1,2,5,45,90):
 cmd=['godot','--path','/dev/shm/havenline-world/Game','--verbose','--headless','--audio-driver','Dummy','--fixed-fps','60','--quit-after',str(i)]
 r=sp.run(cmd,env=e,capture_output=True,text=True,timeout=35)
 rows=(r.stdout+r.stderr).splitlines()
 lines['accelerated_source_'+str(i)]={'exit':r.returncode,'details':[v for v in rows if 'leak' in v.lower() or 'still in use' in v.lower()][:45]}
o=P.Path('/workspace/shared/downloads/Havenline/critic-95/Audio-and-delivery/Exit-diagnostics.json')
o.write_text(json.dumps(lines,indent=2)+'\n')
