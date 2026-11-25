# Exact 52-joint whole-arm opening: HOLD after static two-link authoring

Detached specimen/hypothesis only. No modeled geometry, bind, weight, UV, texture, material, torso joint, left/right assignment, character identity/scale, or original shaft edit. Existing weighted torso skin can still move, so that is an explicit fail gate. The complete arm subtree is moved around each fixed shoulder in a single paired *open* attempt. This replaces, rather than retunes, the prior rejected fixed-elbow rotations, where newly moving forearm faces clipped stationary upper sleeve faces. Matching elbow/upper surface motion relative to the forearm is the reason for using a whole-arm construction.

Source is the exact owner 52-joint rig, v2 skin, original 512-facet axe with immutable grip stations 124R/276L, and frozen right palm. The prior exact anatomical wrist targets are used only to define one outward direction on each original shoulder-to-wrist sphere. No axis/position scan, offset search, tool scale or tolerance for handle slide/roll is used. The pose uses one scalar finite support-root equation over the actual complete shaft geometry for each side. Given each target wrist point at the original reach, the elbow is reconstructed from the real two-link position sphere/circle intersection and the original elbow pole transported by the coordinated arm rotation. Both link lengths and the elbow bend are preserved at numerical precision. This is structurally different from turning a fixed elbow outward. The applied deltas concern upper arms (not clavicle/torso poses); wrist and digits inherit unchanged local quaternions. Mixed skin rows are independently checked against the pinned original chest-author torso mask, not dismissed merely because their bones still have a torso majority.

A complete source tool AABB and strict finite intersection check plus solid winding checks compare the raw and exact right-authored pressure geometry against all axe facets. Local cuff and pressure-seam constraints are evaluated following their own relative movement, not against the rejected held start in world coordinates. Relative-rigid body groups compare nonincident posed source shell intersection cases, and immutable chart rows are checked separately; these numerical checks are not actual pixels, exterior contours or a physically exhaustive snapshotted pose validation. No effect on lower body or source mesh/UVs is allowed. The output fingerprint identifies the speculative static coordinates reconstructed by the test, not an accepted pose or asset export. No renderer, Godot, Blender, paid actions, or remote writes.

## Exact outcome, no promotion

Both forearm/upper-sleeve pairs named in the two former rejects remain nonintersecting in the coordinated solve (e.g. right 44477/51156 and 44477/51158). Both original exact cuff rows (642R and 588L) move rigidly in their new local poses within 0.063 µm; closed shaft checks again yield 298→0 strict and 631→0 contained character/patch rows, with the actual axe and band positions unchanged. Exact source OPEN rotations are 18.345°R and 3.005°L, elbow sphere/circle errors below 6e−17 m, both original elbow bends and link lengths unchanged, and reserves 165.286/95.415 mm. Palm anchor normal gaps remain 116.896/15.014 mm: this is not a contact or grasp.

It still rejects two hard conditions. Relative-moving body strict pairs go from 364 to 255, but 334 old pairs cleared and **225 entirely new** pairs appeared. The first independently evaluated positive controls include source chest coat 556546 versus moving left upper sleeve 674738 (original pair clear). More importantly **2,291 original torso-author-chart rows move** through existing mixed shoulder influences (R 1,131; L 1,160), up to 2.8995 mm, even though all 229,322 central core vertices, lower body and torso joint matrices remain exact. Do not treat a lower total intersection count or unchanged torso bone as rigorous torso preservation. The original weights and geometry were untouched.

The next distinct path would require a freshly bounded, pose-compatible **shoulder transition strategy** that keeps the protected torso chart and real silhouette exact, or explicit approval for only the outer garment transition to move once characterized. This evidence does not show that all whole-arm or compensated alternatives are impossible, and does not authorize changing garments/weights. No further offset/axis variation or shot is queued from this packet. Contact/release, actual motion, visible cloth and replay through native rig remain on HOLD.

To reproduce alongside the pinned predecessor packages:

```sh
bash run.sh /path/to/exact/held_owner.npz > replay.json
cmp replay.json result.json
bash controls.sh /path/to/exact/held_owner.npz > controls-replay.json
cmp controls-replay.json controls.json
sha256sum -c SHA256SUMS
```
