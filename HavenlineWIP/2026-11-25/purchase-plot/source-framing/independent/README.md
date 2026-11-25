# Independent Level 1 pad source-framing recheck

**Hold camera-only RC2 promotion.** Reproduced the exact sealed builder packet
`8f04062ef372b907ba003943b0933cf64d526f3d70091df94b5c491200c70c34`
byte-for-byte (builder result SHA-256
`02668eb39de828c44559c6a80294193d22e4d3b97351a4567fa2440764adfdd1`).
A separate direct world-space Möller–Trumbore ray predicate reproduced all
26 selected wood/digit cases under four camera controls, including RC2
(345/759 and 0/433 blocked at 1.35 m, 759/759 and 198/433 at .90 m).
The two implementations use the same previously captured pose, terrain and
authored SVG input, not independent captures. Reproduce from this directory:
`python3 recheck.py ../hvn-l1-plot-source-framing-v1`.

Direct Git inspection of playable `11c14a1c41971067c7dc97db69375f720a408f68`
confirms `previews/integrated_opening.gd` calls `install_exact()`, which loads
`purchase_pad_v5.glb` through `pad_v5_view.gd`; both V6 SVG and
`construction_plot_ground.gd` are absent from that commit. This review does
not promote V6/RC2 or show that the pinned V5 shares the RC2 failure.

The .90 m stance has real V6 native ordinary-input history (logged actual
planar range .90022665 m and 3D range .90117103 m, no receipt; observer walks
the south leg before crossing authorized purchase range). The ray study
rebases a 96,001-triangle skinned Character 1 idle pose from a separate 11c
counter fixture to that logged foot position and yaw; it is not proof of
the actual dynamic V6 gait/body or a same-build RC2 attempt. Mathematically
same-basis orthographic pan/scale cannot clear a particular occluded
world-space ray when it remains in the frustum. Crop, clipping, symbol
pixel size, shaders/opacity and the whole-field geometry can change the
result viewers see; no raster legibility or mobile determination was made.
Sampled pitch/width combinations do not eliminate all possible viewpoint
or artwork solutions. No Godot, new renders, scores, or playable code
changes. Next: get exact V5 ordinary visible route and real phone-size
capture; do not substitute the detached candidate or change payment.
