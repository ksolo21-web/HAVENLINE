# V4 hinge relief: continuous geometric proof, art admission HOLD

The independent witness observed real post/leaf triangle crossings, not merely proxy overlap. For mirrored leaves and both gate axes let u be length from hinge toward gate center and z authored depth. During the opening, the inward signed x' is u cos(theta)+z sin(theta) and z' is -u sin(theta)+z cos(theta). Each exact seated R17 post is wholly x' <= -8.000 mm and |z'| <= 193.088 mm in this frame, independently of its Y offset and orientation-only repair. At any 0..90-degree stock pose with u>=0 and x'<0, z'<0 and |z'|>=u (by inverse rotation). Thus these two cases together guarantee swept clearance of actual surfaces:
- u<=194 mm: keep every triangle at z>=-6 mm; minimum x-plane gap 2 mm.
- u>=194 mm: any point with x'<0 is at least 0.912 mm outside the post cross-axis envelope regardless of its depth. 
This covers all continuous rigid motion, not just simulation samples, and preserves immutable hinges, stops, colliders, timing, terrain and threshold posts. It is conservative across components.

One localized numerical witness split source triangles at u=194mm, u=225mm and z=0. It holds u/Y exact, keeps the entire front half and closed center seam unchanged, and tapers depth-only relief in the 31mm exit zone. Both mirrored halves satisfy the sufficient sweep test. The witness has 2,274 triangles per half, not the original admitted 1,360, and does not imply native/raster or assembly approval. No OBJ or runtime adapter was written.

Reject this relief as art. The hinge beam, hardware and both rope loops lose about 91.3% of their back-facing depth. The formerly symmetric ~134mm rope section becomes an asymmetric ~72.8mm (46% full-depth loss); metal 138→75mm. At stock 720p/13m orthographic view, the largest 63mm coordinate shift yields up to 3.49px projected travel, not a raster score or evidence of invisibility. Seven material groups and 699 witness triangles per side are affected. Do not install or weaken the source admission for this witness.

A genuinely different local route would use asymmetric unwarped hinge hardware authored on the safe face with a full wood flange. Check actual component solids, normal-camera projection and real sweep at each seating; do not alter the original gates to fit the donor. This sufficient test does not rule out finer material-specific geometry. Leave stock fallback and source intact.

Replay with OPENBLAS_NUM_THREADS=1 python check_relief.py EXACT_GRAFT EXACT_CRITIC OUTPUT_FOLDER. The check imports the frozen critic geometry-reader prefix to verify exact source hash and placement.
