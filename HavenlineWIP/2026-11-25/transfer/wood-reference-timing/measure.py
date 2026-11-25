import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
record=json.loads((root/'measurement.json').read_text())
assert len(sys.argv)==3, 'measure.py <124510> <124839>'
for path, expected in zip(sys.argv[1:],record['sources']):
 with open(path,'rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==expected['sha256']
 assert Path(path).stat().st_size==expected['bytes']
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=time_base:frame=best_effort_timestamp,best_effort_timestamp_time','-of','json',sys.argv[1]]))
assert probe['streams'][0]['time_base']=='1/90000'
for use in record['events']:
 frame=probe['frames'][use['frame0']]
 assert frame['best_effort_timestamp']==use['pts']
 assert float(frame['best_effort_timestamp_time'])==use['seconds']
 print(f"{use['frame0']}  {use['seconds']:.6f}  {use['label']}")
pts = {e['frame0']: e['pts'] for e in record['events']}
for a,b in [(795,804),(795,820),(795,822),(793,822)]:
 print(f'{a} to {b}: {(pts[b]-pts[a])/90000:.6f}s')
print("PASS exact source, video time base and event witness PTS; observation labels require visual replay")
