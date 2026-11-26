from pathlib import Path
import socket,struct,sys,subprocess as sp,json,sys,threading
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=True)
fps=int(sys.argv[2]);hz=48000
s=socket.socket();s.bind(('127.0.0.1',0));s.listen(1)
(out/'socket-port').write_text(str(s.getsockname()[1]))
a=sp.Popen(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(hz),'-ac','2','-i','pipe:0','-c:a','flac',str(out/'complete-mix.flac')],stdin=sp.PIPE)
v=None
c,_=s.accept(); f=c.makefile('rb',buffering=131072);frames=[];finish={};n=0
try:
 while True:
  h=f.read(8)
  if not h:break
  hl,sz=struct.unpack('!II',h); header=json.loads(f.read(hl)); data=f.read(sz); assert len(data)==sz
  if header['type']=='audio':
   assert header['offset']==n and len(data)==8*header['samples']
   a.stdin.write(data);n+=header['samples']
  if header['type']=='picture':
   if not v:v=sp.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(fps),'-c:v','mjpeg','-i','pipe:0','-c:v','libx264','-threads','2','-preset','veryfast','-crf','17','-pix_fmt','yuv420p',str(out/'picture-track.mp4')],stdin=sp.PIPE)
   v.stdin.write(data)
   if not frames or frames[-1]['chapter']!=header['chapter']:
    (out/('shot-%04d.jpg'%len(frames))).write_bytes(data)
   frames.append(header)
  if header['type']=='finish':finish=header
finally:
 a.stdin.close();assert a.wait()==0
 if v:v.stdin.close();assert v.wait()==0
(out/'capture-packets.json').write_text(json.dumps({'fps':fps,'rate':hz,'samples':n,'finish':finish,'frames':frames},indent=1))
assert finish and finish['frames']==len(frames) and finish['lost']==0 and abs(finish['mix_hz']-hz)<1
