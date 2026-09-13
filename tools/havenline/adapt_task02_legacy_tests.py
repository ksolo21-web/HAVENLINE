"""Apply two scope-driven terrain assertions; preserve all existing test coverage.
This file is an installer for the existing test only; not game or visual approval.
"""
from pathlib import Path
p=Path('HavenlineGodot/tests/test_outpost.gd');s=p.read_text()
old='mesh.get_faces().size()==30752*3'
new='mesh.get_faces().size()==int(Surface.HALF*2.0/Surface.STEP)*int(Surface.HALF*2.0/Surface.STEP)*6'
if new not in s:
    assert s.count(old)==1, 'Legacy topology assertion changed; inspect before modifying'
    s=s.replace(old,new)
old='\t\tnormals_ok=normals_ok and normals[i].y>.9'
new='\t\t# T02: the submerged nonwalkable bank has separate normal/winding tests.\n\t\tif Surface.lake_distance(Vector2(v.x,v.z))>1.2:\n\t\t\tnormals_ok=normals_ok and normals[i].y>.9'
if new not in s:
    assert s.count(old)==1, 'Legacy dry-slope assertion changed'
    s=s.replace(old,new)
p.write_text(s)
