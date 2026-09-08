#!/usr/bin/env python3
"""Integrate T01 only; fail rather than overwrite a concurrent main.gd edit."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'HavenlineGodot/scripts/main.gd'
s=p.read_text()
if 'const ReferenceForest = preload(' in s:
    raise SystemExit('T01 already installed; inspect rather than applying twice')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f25263c0422e6459d769245ff078c7ae18abee2f3a890375bc8264088b167dc6','main.gd changed: preserve concurrent work'
a='const Scenery = preload("res://scripts/scenery_batch.gd")'
assert s.count(a)==1
s=s.replace(a,a+'\nconst ReferenceForest = preload("res://scripts/reference_forest.gd")\nvar reference_forest_evidence: Dictionary = {}')
a='\t\tpath = "res://assets/environment_v2/" + asset.trim_prefix("world/") + ".glb"'
assert s.count(a)==1
s=s.replace(a,a+'\n\t\tif asset.begins_with("world/pine_"):\n\t\t\tpath = "res://assets/reference_forest/" + asset.trim_prefix("world/") + ".glb"')
a=s.index('\t# Irregular woodland groups');b=s.index('\tbuild_environment_dressing()',a)
s=s[:a]+'\t# T01 reference forest; no change to resource actions or later-task layout.\n\treference_forest_evidence = ReferenceForest.build(self)\n'+s[b:]
a='\treport["environment_revision"] = ENVIRONMENT_REVISION'
assert s.count(a)==1
s=s.replace(a,a+'\n\treport["reference_forest"] = reference_forest_evidence')
p.write_text(s)
print('T01 runtime applied. No independent critic or performance approval.')
