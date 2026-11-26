# Character 1 / Level 1: rejected exact opposed-contact key and center correction

No playable changes, render, engine session, external rigging or gait approval. Source is exact Havenline Level 1 commit `11c14a1c41971067c7dc97db69375f720a408f68`, not the default launch scene. This diagnostic uses the authored initial transform/camera and original indexed snow, not a native post-collision settled frame.

1. `stage/`: one new geometry solve from the exact fresh 52-joint binding on the exact stock visible art. Both soles can touch original terrain while the selected left contact marker and center still fail.
2. `feasibility/`: planar geometric feasibility against the failed key's original measured footprint. No second geometry solve and no claim of changing pose.
3. `correction/`: exactly one subsequent evaluation of the frozen pelvis-only target. The planned center result reproduced; left marker still failed and actual mesh crossings increased. Do not repeat another pelvis placement variation or use this as a gameplay model.

`provenance.json` records the original and portable manifests. The three result receipts are exact unchanged bytes. Portability edits only locate and check dependencies; no solve differs. No original game files, meshes, pose/skin payloads or native logs are included.

## Replay identical evidence (no Godot engine)

Inputs must be local, exact and authorized. Check source commit and use its Level 1 project root. Regenerate the double-sealed fresh rig from `../level1-clean-character1-rig-source-v1/evidence/build.py` using the exact original asset; its reported neutral bind / skin hashes are checked by every stage. This is a new held key, not a replication of the earlier rejected V3 pose.

Set absolute paths to the pinned source and your generated rig directory; set tool inputs to the archived sibling scripts:

- `HAVENLINE_PROJECT`: pinned Level 1 project root.
- `HAVENLINE_RIG`: regenerated original fresh 52 rig directory.
- `HAVENLINE_ARCHIVED_GLB_PARSER`: `../level1-c1-fastener-mounts-v1/inspect_source.py`.
- `HAVENLINE_ARCHIVED_GROUND_SUPPORT`: `../level1-clean-rig-grounded-v3-result/evidence/support.py`.
- `HAVENLINE_ARCHIVED_GROUND_EVALUATOR`: `../level1-clean-rig-grounded-v3-result/evidence/evaluate.py`. Only the verified strict triangle-overlap function is loaded, not the old V3 entrypoint, control inputs or output.

With NumPy and SciPy available and `OPENBLAS_NUM_THREADS=1`, run from this package root:

```sh
sha256sum -c SHA256SUMS
(cd stage && python stage.py)
(cd feasibility && python center_intake.py)
(cd correction && python once.py)
```

Compare stdout to each directory's exact `result.json`. The same holds remain even if all three computations reproduce.
