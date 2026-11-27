"""Write a desktop-readable pack containing the signed APK's unmodified Godot assets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
from hashlib import sha256, file_digest
import shutil,sys,json
apk,destination,report=map(Path,sys.argv[1:])
hashes={}
with ZipFile(apk) as source, ZipFile(destination, 'w', compression=ZIP_STORED) as pack:
    for info in source.infolist():
        if info.is_dir() or not info.filename.startswith('assets/'): continue
        name=info.filename.removeprefix('assets/')
        if name in hashes or name.startswith('/') or '..' in Path(name).parts: raise ValueError(name)
        digest=sha256()
        with source.open(info) as reader,pack.open(name,'w') as writer:
            while chunk:=reader.read(512*1024):
                digest.update(chunk);writer.write(chunk)
        hashes[name]=digest.hexdigest()
with ZipFile(destination) as pack:
    for name,checksum in hashes.items():
        with pack.open(name) as part: assert file_digest(part,'sha256').hexdigest()==checksum
with apk.open('rb') as f: apk_sha=file_digest(f,'sha256').hexdigest()
report.write_text(json.dumps({'apk_sha256':apk_sha,'apk_bytes':apk.stat().st_size,'packed_files':len(hashes),'identical_files_verified':len(hashes),'temporary_pack_bytes':destination.stat().st_size,'scripts':{k:v for k,v in hashes.items() if k in ['project.binary','field_opening.gd','field_opening.gdc','orbit_opening.gdc','weapon_orbit.gdc','field_enemy.gdc']}},indent=2)+'\n')
