# Level 1 fence V4 lower-front crossing repair (WIP)

Rebuild source only; no in-game approval. With Python 3 and NumPy, from this directory run `python build.py /path/to/33036.png /path/to/approved-wall-envelope.obj` (keep the matching 33037.png beside 33036.png), then `python splice.py /path/to/exact-v3-textured-panel-directory`. The inputs are hash-pinned. The second step needs the original V3 OBJ/MTL/atlas, not published here. This recipe reproduced the exact V4 OBJ and splice result byte-for-byte using the matched inputs. Do not reuse an approximate asset with the same filename.

Only the two lower front rope curves change. Face and UV indices are preserved, as are timber, rail, snow, upper/rear geometry and the texture. Source-only normal camera projection increases the lower-leg separation, but a matched native picture is still required before grading. No raw references, textures, third-party models, release, or commerce.
