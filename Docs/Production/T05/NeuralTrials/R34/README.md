# R34 — Genuine neural image-to-3D experiment (REJECTED)

This is the first **true neural** reconstruction run in GitHub from the owner's exact original cooker render. It is **not a passing T05 cooker**.

- **Source:** [front three-quarter owner original](../../../../Art/SourceReferences/T05/32451.jpg), SHA-256 `70e9e04c329797490b19aaa383865a5a2e20129bd1e0250a6997b170fb0510e4`.
- **Method:** TripoSR, pinned MIT-licensed upstream; CPU on free GitHub Actions runner.
- **Actual candidate:** [GLB (unapproved)](T05_neural_owner_front_UNAPPROVED.glb), SHA-256 `4c8c4b52b838e628d2bb01cf21e281ce9b5594cef7ac019c7c941e887abf0088`, 21,888 triangles, nonwatertight.
- **Actual native-rendered critique:** [Godot side-by-side](R34_REAL_GODOT_SOURCE_CRITIC_FAIL.jpg) (Godot 4.7.2, Mesa software OpenGL, 960×960, four captures).
- **CI run:** https://github.com/ksolo21-web/HAVENLINE/actions/runs/40771079678
- **Technical audit:** [R34 JSON receipt](R34_RECONSTRUCTION_AND_CRITIC.json).

### Art verdict — FAIL
The single-image model badly distorts wood, snow, food and the mechanical housing; its geometry is badly misoriented and it does not match the **authoritative side or rear owner renders**. Those three sources are available in Git, but TripoSR inferred geometry from only the front view. No source camera registration or multiview reconstruction occurred.

### Important renderer detail
TripoSR exports vertex colors. Initial native Godot import looked plain white until `StandardMaterial3D.vertex_color_use_as_albedo = true` was explicitly applied on the imported mesh. The reviewed Godot screenshots were **captured after** that correction. Renderer is software, not proof of Android frame rate.

### Next
A multiview-conditioned 3D method must consume all three views coherently. Preserve this run only as proof that the free GitHub pipeline runs real neural inference; do not promote it or claim critic acceptance.

**Shipping game files unchanged.** T05 is still blocked by source fidelity, independent review, owner approval, and phone performance testing.
