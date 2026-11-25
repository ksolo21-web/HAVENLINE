# Exact native-derived clipping views, presentation-only repair

One bounded Blender CPU rerender of the predeclared exact original 0.375 s chop pose (ratio 0.55147058) from the native PR #108 offset-only trace. The extractor was unchanged, and the collected exact triangle-coordinate intermediate was byte-identical to the first diagnostic; SHA-256 witness in `exact-geometry-sha256.txt`. No pose, asset, relative geometry, camera, placement, or scale changed. Only lighting strength and the diagnostic palette/ambient-emission mix changed. The light repair makes the shaft, gloves and both cuffs distinguishable. Red marks exact previously intersecting glove/cuff faces; it does not measure penetration depth or imply all parts of those faces intersect. Full-versus-lower-shaft counts remain gloves L 88/36 and R 122/74, cuffs L 115/63 and R 226/144. Full hammer/axe head crop, noisy low sample count, and detached surroundings are intentional diagnostics.

Both 850×720 original render outputs and the portable JPEG derivatives were visually inspected. The two angles clearly show cuff geometry intersecting the warm-colored shaft, with blue gloves and gray cuffs distinguishable. Near-white computed on PNG foreground is zero in both (previous ~62% and ~77%); see `pixel-check.txt`. JPEG derivatives are shareable evidence only, not final art, a real game capture, phone data, or a release signoff. No GPU, gameplay, or additional fit variant. Do not share the intermediate exact coordinate JSON, raw assets, or unsanitized logs.

```sh
python3 extract.py /path/to/exact/pr108/HavenlineLevel1 /path/to/sealed/samples.log.gz > /path/to/disposable/geometry.json
blender -b -t 2 --factory-startup --python-exit-code 2 --python blender_view.py -- /path/to/disposable/geometry.json /path/to/disposable/output
# From the Blender output folder:
python3 /path/to/pack_views.py
```

Log redacts the two local saved-file paths. Imported geometry remains detached and is carried only by the exact frozen source and pose trace, not as an asset in this packet.
