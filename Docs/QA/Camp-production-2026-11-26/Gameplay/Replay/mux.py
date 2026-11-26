from pathlib import Path
import subprocess as sp,sys,json,hashlib,itertools,numpy as np
from scipy import signal
run=Path(sys.argv[1]);movie=Path(sys.argv[2]);fps=int(sys.argv[3])
rec=json.loads((run/'capture-packets.json').read_text()); frames=rec['frames'];hz=rec['rate']
chunks=[]
for i,f in enumerate(frames):
 if i==0 or f['chapter']!=frames[i-1]['chapter'] or f['engine_frame']!=frames[i-1]['engine_frame']+1:chunks.append({'title':f['chapter'],'first':i,'last':i,'source':f['engine_frame'],'source_tick':f['physics_tick']})
 else:chunks[-1]['last']=i
stereo=np.frombuffer(sp.check_output(['ffmpeg','-v','error','-i',str(run/'complete-mix.flac'),'-ar',str(hz),'-ac','2','-f','s16le','-']),np.int16).reshape(-1,2)
samples=[];lines=[';FFMETADATA1'];fini=0
for c in chunks:
 # Track the frame on the original Godot 48k/24fps clock. The native bus hands
 # the monitor samples in 512-frame blocks, so packet availability can differ.
 s=round(c['source']*hz/fps);length=round((c['last']-c['first']+1)*hz/fps); x=stereo[s:s+length];assert len(x)==length
 c['audio_original_samples']=[s,s+length];samples.append(x.tobytes())
 lines+=['[CHAPTER]','TIMEBASE=1/'+str(fps),'START='+str(c['first']),'END='+str(c['last']+1),'title='+c['title']]
meta=run/'chapters.ffmeta';meta.write_text('\n'.join(lines)+'\n')
sp.run(['ffmpeg','-v','error','-y','-i',str(run/'picture-track.mp4'),'-f','s16le','-ar',str(hz),'-ac','2','-i','pipe:0','-f','ffmetadata','-i',str(meta),'-map','0:v','-map','1:a:0','-map_chapters','2','-c:v','copy','-c:a','aac','-b:a','160k','-movflags','+faststart',str(movie)],input=b''.join(samples),check=True)
probe=json.loads(sp.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(movie)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video'); a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert int(v['nb_read_frames'])==len(frames) and a['channels']==2 and int(a['sample_rate'])==hz
dec=np.frombuffer(sp.check_output(['ffmpeg','-v','error','-i',str(movie),'-map','0:a:0','-f','f32le','-ar',str(hz),'-ac','2','-']),np.float32).reshape(-1,2)
original=np.frombuffer(b''.join(samples),np.int16).reshape(-1,2).astype(float)
for c in chunks:
 start=int(c['first']*hz/fps);end=int((c['last']+1)*hz/fps);ix=min(1000,(end-start)//4)
 c['stereo_correlation']=[round(float(np.corrcoef(original[start+ix:end-ix,i],dec[start+ix:end-ix,i])[0,1]),5) for i in (0,1)]
assert all(min(c['stereo_correlation'])>.90 for c in chunks),chunks
receipt={'movie':movie.name,'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'native':[v['width'],v['height']],'fps':fps,'frames_decoded':len(frames),'elapsed_seconds':len(frames)/fps,'audio_rate':hz,'audio_channels':2,'mixer_frames_discarded':rec['finish']['lost'],'camera_paths':list({f['camera'] for f in frames}),'render_scales':list({f['render_scale'] for f in frames}),'chapters':chunks}
movie.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(movie, len(frames),'frames,',len(chunks),'chapters, native audio correlation',min(min(c['stereo_correlation']) for c in chunks))
