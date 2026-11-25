# Wood-flight art intake: studio source comparison
Offline Blender render, not a character, transfer, current game camera, visual grade, or asset approval. Model imports use identical lighting and normalized largest bounding dimensions for clear visual comparison, not actual relative game scale. No source model is modified or promoted.

Pinned project commit 11c14a1c41971067c7dc97db69375f720a408f68. Source inputs:
- HavenlineGodot/assets/environment_v2/log.glb with SHA-256 a2aaa91eb0f502a12980b4ce6cffab505fcd94fa254ddba6c32e77919d0cb741 (Git blob 9e43907a074c79f7679de1573146eb8ce317aa8d). Older R9 environment asset, pale cut and simpler tapered bark, no per-flight admission.
- HavenlineGodot/assets/world/log.glb with SHA-256 29667a7def59644692cc35e5c766d095af169169ab62ba160726db4ad1ffe303 (Git blob ad878fd1f025a6980679c5590e315f633ed5500d). Original file itself is an unapproved art candidate. Smoother simple cylinder; no per-flight admission.
- HavenlineLevel1/assets/studio/wood_bundle_v3.glb with SHA-256 1004ea2f41751bf79ad10ab0165c60a05e5ee581d35095913a0794f16931abd9. Exact hydrated opening carry asset. Three orange-brown logs and rope, visibly closer to the current direction. Used as a whole, not as individual pieces.

Recommendation: preserve the richer original carry design as the single-log visual reference; do not repurpose a legacy log just because it exists. Any derived or new transfer item needs exact identity, oriented scale and pivot and independent art/role checks before consideration. This comparison does not create a derivative, change attachments, choose a receiving footprint, or prove 52 on screen.

Reproduce with Blender background using render.py, the parent directory containing the three exact source files at their repository-relative paths, and FILE.png. For the supplied comparison layout, place its image as wood.png next to layout.py and run with Pillow.
