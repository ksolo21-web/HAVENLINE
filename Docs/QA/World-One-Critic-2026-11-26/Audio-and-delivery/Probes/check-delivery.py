import subprocess as sp,pathlib as P,json,os,hashlib,tarfile,zipfile
p=P.Path('/workspace/shared/downloads/Havenline'); b=p/'world-one-mining/Build'; o=p/'critic-95/Audio-and-delivery'
src=P.Path('/dev/shm/havenline-world/Game'); db='/dev/shm/havenline-world/published.git'
m=json.loads((b/'Reviewed-files.json').read_text()); commit=m['commit']
def run(cmd,**kwargs):
 r=sp.run(cmd,capture_output=True,**kwargs);return [r.returncode,(r.stdout+r.stderr).decode(errors='replace').strip()]
def hashfile(file):
 h=hashlib.sha256()
 while chunk:=file.read(1048576):h.update(chunk)
 return h.hexdigest()
compare={}
for n,val in m['files'].items():
 git=sp.check_output(['git','--git-dir='+db,'show',commit+':HavenlineLevel1/'+n])
 assert hashlib.sha256(git).hexdigest()==val
 compare[n]=(src/n).exists() and hashfile((src/n).open('rb'))==val
reports=dict(commit=commit,source_files=len(compare),mismatches=[n for n,v in compare.items() if not v],source_scene=m['scene'])
packages={f.name:hashfile(f.open('rb')) for f in b.iterdir() if f.suffix in ('.gz','.apk')}
saved=json.loads((b/'Package-verification.json').read_text())
assert all(saved['packages'][n]['sha256']==v for n,v in packages.items())
reports['package_hashes']=packages
private=P.Path('/tmp/hl-critic-audio');env=os.environ.copy()
for k in ('HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME'):
 env[k]=str(private/k.lower()); P.Path(env[k]).mkdir(exist_ok=True)
androidsdk='/tmp/haven-android-tools/sdk'
apk=next(b.glob('*.apk'))
reports['apk_signature']=run([androidsdk+'/build-tools/35.0.1/apksigner','verify','--verbose','--print-certs',str(apk)])
reports['apk_alignment_16k']=run([androidsdk+'/build-tools/35.0.1/zipalign','-c','-P','16','4',str(apk)])
with zipfile.ZipFile(apk) as z:
 reports['android_zip_crc_error']=z.testzip();reports['android_abi']=[n for n in z.namelist() if n.startswith('lib/')][:12]
with tarfile.open(next(b.glob('*.gz')),'r|gz') as tar:
 for member in tar:
  if not member.isfile(): continue
  if member.name.endswith('.sh'):reports['launcher']=tar.extractfile(member).read().decode();continue
  assert member.size<400*1024**2
  if member.name.endswith('x86_64'):
   elf=private/'Havenline-Mining.x86_64';fd=os.open(elf,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o700);h=hashlib.sha256();stream=tar.extractfile(member)
   while data:=stream.read(1048576):
    h.update(data);os.write(fd,data)
   path=str(elf);os.fchmod(fd,0o700);os.close(fd)
   reports['linux_binary_sha256']=h.hexdigest()
   assert h.hexdigest()==saved['linux']['archive_elf_sha256']
   reports['linux_packaged_headless']=run([path,'--headless','--audio-driver','Dummy','--quit-after','90'],env=env,timeout=115)
   elf.unlink()
adb=androidsdk+'/platform-tools/adb'
reports['adb']=run([adb,'-P','5045','devices','-l'],env=env);run([adb,'-P','5045','kill-server'],env=env)
reports['hardware_paths']={n:P.Path(n).exists() for n in ['/dev/dri','/dev/snd','/dev/bus/usb','/sys/class/drm','/dev/kvm','/dev/nvidia0']}
reports['pci_display_devices']=[str(q.parent) for q in P.Path('/sys/bus/pci/devices').glob('*/class') if q.read_text().startswith('0x03')]
reports['git_audio_reference_assets']=run(['git','--git-dir='+db,'ls-tree','-r','--name-only',commit,'Docs/Design/ReferenceVideoLock'])[1].splitlines()
(o/'Package-and-device-audit.json').write_text(json.dumps(reports,indent=2)+'\n')
