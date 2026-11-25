# Reproduce the rejected broad boot repair

Use a disposable directory. Run `collect.py` in Blender with the exact stock Character 1 GLB as the final argument (SHA-256 checked by the script). Run `solve.py` with NumPy and SciPy to reconstruct the diagnostic corrected arrays, then `attribute.py` with NumPy and `check_bvh.py` in Blender to reproduce the evidence. The intermediate `.npz` arrays are generated, not checked in. The archived candidate failed the combined edge and face-area checks and has no export or gameplay hook.
