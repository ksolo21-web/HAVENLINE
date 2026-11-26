# Winter Welcome two-handed harvest review

**Scoped verdict.** Both swings read more naturally at the opening camera. Shoulder and chest rotation carry the tools through a raised windup and a lower strike. The axe in particular no longer holds the leading elbow at almost one angle. Both hands stay braced on the shaft. The head of each tool overlaps its target shortly before the authored strike, and the pick enters the unbroken rock deeply. Timing and penetration still have room for polish.

Reviewed character GLB SHA-256 `5dec020c6e8c8d18ee58332e620aac53ad850fd3f2ae4f9778329b531ba6ce72`. Footage used 250 native 1280×720 game readbacks in total, including 95 swing records per tool. The two photos show four corresponding phases at the game's camera, with bone centers overlaid in duplicate rows.

| Check | Independent finding |
| --- | --- |
| Character and tool identity | Winter Welcome matches the selected Meshy source geometry, UVs, material and embedded texture bytes. Both fitted tools retain their original Meshy topology, UVs and image payloads. The head shapes match the generated originals to within 0.005 mm after alignment. |
| Arms and body | Left elbow extends and flexes across 131.1–142.0° for axe and 133.1–147.0° for pick. Right elbow spans 134.4–162.2° and 141.9–151.8°. Chest turns 38.0° and 31.3°. Knees absorb the stance change, with weighted heel/toe motion below 0.015 mm. |
| Limb and prop clearance | All 38 tested region pairs stayed clear across 178 samples per clip at 120 Hz. This covers the selected glove, arm, clothing and tool regions. Some tightly folded garment edges near the hips still more than double their rest lengths. |
| Grip | In the exported animations the maximum nearest shaft-to-digit gap for the sampled material vertices across all ten fingers was 1.13 mm for axe and 1.63 mm for pick. In the actual Godot readback, including held and swing phases, the maximum closest-finger gaps were 2.87 mm and 3.59 mm across 125 visible frames per tool. Maximum shaft intrusion was 1.90 mm and 2.30 mm. |
| Target contact | At the 0.717 s marker both tool heads overlap actual rendered triangles. The axe edge is 1.83 mm inside the trunk and the pick tip is 51.77 mm inside the full-size rock. At 0.733 s, when the game awarded the strike, depths were 3.64 mm and 9.42 mm, respectively. The rock shrinks by 18% when the strike succeeds. |
| Timing limitation | On the approach, the first head-face overlap was at 0.633 s for axe and 0.700 s for pick. The broader axe head reaches the tree before its designated edge point. A claim that contact begins exactly at the marker would overstate the evidence. |

The timing measurements apply to this stationary approach to one tree and one rock. The reviewed owner reference stills show hauling and delivery. An original live-action swing sequence was unavailable for timing comparison. A whole-rig release score, other stances, gait transitions and phone performance remain unverified.

[Measured live grips](Independent-Live-Grips.json.gz) · [Gameplay phases](Independent-Game-Frames.jpg) · [Previous phases](Independent-Previous-Game-Frames.jpg) · [Target triangles](Independent-Target-Triangles.json) · [Joint measurements](Independent-Joint-Motion.json) · [Tool provenance](Independent-Tool-Identity.json)
