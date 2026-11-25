"""Create the exact detached PR108 socket-storage patch; emits no modified game file."""
import argparse, difflib, hashlib
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('original', type=Path, help='exact PR108 character_kit.gd')
args=p.parse_args()
raw=args.original.read_bytes()
assert hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()=='e36c676137882ac5d3e195645b78e30ab6c476fd'
src=raw.decode()
def change(code, before, after, count=1):
    assert code.count(before)==count,(before,code.count(before))
    return code.replace(before, after)
out=change(src,'const MOVE_MIN := 0.08\n','const MOVE_MIN := 0.08\nconst SOCKET_OFFSET := ^"LocalOffset"\n')
out=change(out,'_sheath.global_transform','_socket_world_transform(_sheath)',2)
out=change(out,'_palm_r.global_position','_socket_world_transform(_palm_r).origin')
out=change(out,'_palm_l.global_position','_socket_world_transform(_palm_l).origin')
out=change(out,'\tattachment.position = local\n\treturn attachment\n',
'''	# Godot replaces the attachment transform on each skeleton update.
	var marker := Node3D.new()
	marker.name = "LocalOffset"
	marker.position = local
	attachment.add_child(marker)
	return attachment

func _socket_world_transform(attachment: BoneAttachment3D) -> Transform3D:
	var marker := attachment.get_node(SOCKET_OFFSET) as Node3D
	return marker.global_transform
''')
assert 'side * 0.08' in out
assert all(line in out for line in ('attachment.name = "Socket_" + bone','attachment.bone_name = bone','_skeleton.add_child(attachment)','var _palm_l: BoneAttachment3D','var _palm_r: BoneAttachment3D','var _sheath: BoneAttachment3D'))
path='HavenlineLevel1/character_kit.gd'
print('diff --git a/'+path+' b/'+path)
print(''.join(difflib.unified_diff(src.splitlines(keepends=True),out.splitlines(keepends=True),'a/'+path,'b/'+path)),end='')
