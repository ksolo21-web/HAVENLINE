"""Verify identities of inspected private evidence; do not emit reference pixels."""
from pathlib import Path
import hashlib,json,sys
full,seek=map(Path,sys.argv[1:3])
samples=[
 (full,'B-008.00.png','8544aee9feba9bdb5d3060ec8449bd2ba07f7ad4092c70599979120e3d09c65b','empty wood glyph visible'),
 (full,'B-010.00.png','10e434c1b949d18f76e9a510c8376895e4996413d7f8ae1b2f3df924aa848e8c','empty wood glyph visible'),
 (seek,'ref275-LOCAL.jpg','a80ea9141d9239f89d4e800d2e187e07a7e23668fb84a2179b4dbf3154ffc78f','empty rear wood pad, airborne object still separate'),
 (seek,'ref28-LOCAL.jpg','b124934d4a04dde304db43c76c72eefda28b3b3c9fb00412e66c3e6f21d27529','low row partly covers printed icon; exposed top/bark and part gold remain'),
 (full,'B-028.00.png','3e983101885a727eb32fcc0d132fcacf8be8c439d2dfefcb267b45326065ee18','original full-frame corroborates partially occluded printed glyph'),
 (full,'B-048.00.png','ccf9a3160f5ead3d472f7540ac980aa60116de609b94954c4b880cf76d78a6dc','dense rows cover central glyph region; lower edge remains visible; some actor-column occlusion')]
print(json.dumps([{'file':n,'sha256':d,'observation':obs} for p,n,d,obs in samples if hashlib.sha256((p/n).read_bytes()).hexdigest()==d],indent=2))
assert all(hashlib.sha256((p/n).read_bytes()).hexdigest()==d for p,n,d,_ in samples)
