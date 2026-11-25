# Exact native shaft and hand transform capture (staged, not run)

PR #108 head 48c6c53a0dfda117ef12c68b32cfe2b3732d5239 only; exact socket-only proposal applied in a disposable archive. No adopted build or production changes. Run only after an individual serial engine grant:

```sh
bash run.sh /path/to/exact/pr108-checkout /path/to/sealed/offset-patch /path/to/shared/Godot-lease > samples.log 2> import.log
```

Natural playback samples once per twelve normalized phase buckets (.07–.95 in 0.08 steps) for carry, chop and mine. No seek, manual mixer tick or forced skeleton update. Missing phase bucket fails rather than duplicating a row. The fixture derives the source hero height-fit with actual imported AABBs and uses a displaced and rotated synthetic actor parent. It invokes exact kit placement explicitly after observing each evaluated clip phase; this isolates placement geometry and does not prove integrated physics-to-animation ordering.

Each JSON sample records left and right sockets and hand attachment coordinates and full axes; immutable anatomical label sentinels, observed height-sort band assignments, configured local bands and their actual world locations; tool node and individual mesh transforms; rig world and evaluated globally composed bone poses in rig coordinates (header includes bone names); hero MeshInstance roots with exact native skin bind transforms and skeletal mappings in the header. Basis arrays are XYZ columns. Point coordinates are native meters. The tool shape comes only from exact SHA-pinned original axe or pickaxe GLB; the trace is sufficient to reconstruct exact posed shaft triangles from those original vertices without copying asset meshes into this packet. Character skin surface reconstruction needs additional validation of imported vertex weights and Godot palette mapping; the header/sample values are inputs, not a solved surface contact test. Do not claim actual low/high contact, pose transitions, thumb/finger closure or quality from this trace. Sampling actions independently after clip guard is not authored transition behavior; inspect a true input-driven carry→chop or mine transition separately.

Scope still excludes grip fit, artwork, renders, hit timing, gfx screenshots and final gameplay acceptance. Retain precise fail/negative controls if later testing fixed anatomical mapping, including a deliberate accepted-same-midpoint identity swap and a shortened/offset haft alternative against exact triangles, not generated stand-ins.

## Executed native run

Godot 4.7.2 exited 0, sampled all 36 observational phases with zero failures; exact imported height fit 1.7863051710. The import log retains known ambient OBJ/PBR notes and no engine errors. `samples.log.gz` holds the exact 38 prefix-tagged output records (header, 36 samples, verdict) extracted losslessly from standard output; no asset bytes. To reproduce the same postprocess on the frozen observations:
```sh
gzip -cd samples.log.gz > frozen-samples.log
python3 contact_inputs.py /path/to/exact/pr108/HavenlineLevel1 frozen-samples.log > observed-replay.json
cmp observed.json observed-replay.json
```
The postprocess checks exact source tool blobs and calculates unsigned nearest point-to-triangle distances using reported native MeshInstance world transforms. The optional deliberately conservative lower-haft subset only accepts triangles with all local vertices at Y <= -0.029 m; it is not the entire handle.

Native thumb/palm socket proxies, not hand surfaces: fitted spans were 329.74 mm carry, 218.70–296.42 mm chop and 188.48–239.47 mm mine. Compared with fixed sorted bands, each axial miss was about 11.56 mm carry, 28.22–67.08 mm chop, and 83.84–109.33 mm mine. All twelve natural carry samples ranked left lower; all twenty-four chop/mine samples ranked right lower. Closest unsigned distances to original full tool mesh were approximately 5.36 mm at both carry sockets, 5.36 mm left and 0.34–5.36 mm right in chop, and 9.43 mm both mine. Cut data do not establish which side of a closed surface the socket lies on, whether the palm intersects, the actual contact bands, or whether any finger closes. Head/trim may influence full mesh minima near transition; examine selected triangles for any contact assertion. Do not infer any art resize or acceptable 80 mm shift. Next independent assessment requires mapping exact native bind indices and weights to the actual hand mesh skin and recomputing triangle/triangle contact or positive clearance at admitted synchronized frames, separately from on-screen device evidence.
