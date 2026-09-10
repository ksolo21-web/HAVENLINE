#!/usr/bin/env python3
"""T02 connection repair only. Refuse concurrent changes; never assign review scores."""
from pathlib import Path
import hashlib,subprocess
FILES={
 'HavenlineGodot/scripts/outpost_surface.gd':('6afb0c9f91b7db4fee322b20de43f5479fac2585a0f0c109eb3cddbf059abb4e','8cc820880d98f600f3004dea563be603dad11104729d324506480b4e63afc7c4'),
 'HavenlineGodot/shaders/outpost_snow.gdshader':('6590af8a5cde0e9708da104fcc99ce7f4898c294abdf7e934ec46e3f4e7ca3ff','69a37930cfcc220fa9f0bbd39f9e3d5fb9f7205c16556ac4d6a726c199950d33'),
 'HavenlineGodot/tests/capture_task02.gd':('f87ceca45210f6420f7fd972665b776dec8b39e937594bd20fe0c08682a7be32','7e00c69fe9951eedbf13d08458eaf2e8e9d90e401b20fbf66c92dc3e5c2421cd'),
 'HavenlineGodot/tests/test_task02_surface_stress.gd':('37e06e6d5a1c1bc8e4e2bdf317edf56341d35c34c936a7c07d6ae2179f63a5f6','5a2bd40cbc42e3fad788fd6fc252cfa7252a847147dc47656e5a8910ebe069e8')}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
if all(sha(name)==values[1] for name,values in FILES.items()):raise SystemExit(0)
for name,values in FILES.items():assert sha(name)==values[0],'Concurrent edit: '+name
patch=Path('Docs/Production/T02/connection.patch')
assert sha(patch)=='c57d8eb096e9d19eaf741dbb32f77365bf4d58a4421f1935d38458432def854e'
subprocess.run(['git','apply','--check',str(patch)],check=True)
subprocess.run(['git','apply',str(patch)],check=True)
for name,values in FILES.items():assert sha(name)==values[1],'Unexpected resulting source: '+name
print('T02 connection geometry and route tests match locally tested files; no review approval.')
