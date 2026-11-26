# Rebuild the V12 garment binding

Use Blender 4.3.2 with NumPy. Supply the editable V9 rig and a new empty output directory.

```sh
blender -b -t 2 -P author_surface.py -- /path/to/V9/Character-1-Rigged.blend /path/to/new-output
```

The script fits the influence of the foot, shin, thigh and pelvis across the cuffs and overlapping lower coat. It keeps the existing bone animation actions, mesh topology, UVs and rest pose. Every source vertex below 90 mm retains its original skin influences. The three supplied V9 actions and source mesh are dependencies.

Godot work copies can import Character-1-Rigged.glb directly. The matching .blend preserves the editable groups and skeletal actions.
