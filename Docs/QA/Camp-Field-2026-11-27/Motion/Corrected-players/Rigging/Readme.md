# Rebuild the three compact player rigs

Python 3, NumPy, SciPy and Pillow are required. Use the unaltered Meshy source GLB and the shipping Character1Fresh.glb controller with the matching recipe. Run from this directory and choose a new output path. The recipe checks both input hashes before writing the fitted GLB.

```bash
python fit_skin.py ../../../References/Owner-identity/Meshy/C2/raw.glb /path/to/Character1Fresh.glb C2-bind.json /tmp/Character2Compact.glb
python asset_proof.py ../../../References/Owner-identity/Meshy/C2/raw.glb /tmp/Character2Compact.glb C2-bind.json
```

Repeat with the C3 and C4 recipe and matching raw GLB. The measured coordinates use metres in a Y-up rest pose, facing positive Z. Each model has its own hip, knee, ankle, foot, shoulder and wrist centers on the shared compact skeleton. The fitter assigns the source colors, UVs, materials and textures to that body's original topology. It binds the hair around the head, gives each boot a separate rolling forefoot and exposes the visible limbs to the field controller.

Character 2 and Character 3 use measured sleeve spans of 0.83 and 0.82 times their standing height. The added reach is distributed across the upper sleeve and forearm. Each mitten translates as a unit. Character 4 keeps the 0.794 span from its raw mesh. The three C2 hood maps restore the original blue garment seen from behind. Each map has its own hash in the C2 recipe.

The proof compares source topology, UVs, material bindings, embedded texture hashes and rest deformation. It also measures the final reach, position changes at the torso, head and lower body and local change across each mitten. The visible gameplay motions are driven by the selected field body's contact tracking and the original compact controller.

[Original asset receipts](../../../References/Owner-identity/) · [Mobile camera and native geometry review](../../../References/Rigs/Current-compact/)
