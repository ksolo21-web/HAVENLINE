# Winter Welcome hand rig and harvesting

**The finger rig, both tool grips and both in-place strikes pass the measured checks. Independent whole-rig score: 8.9/10.** The final export clears the right-sleeve crossings found in earlier versions. The formal whole-character gate remains open on 28 unverified checks for hidden attachments and garment seams.

The reviewed [harvest GLB](../../Rig/Winter-Welcome-Harvest.glb) has SHA-256 `b9b4e98ef7d27ddf5886199e3642c60c0a3bd34aa0c6520eb11e22c75718dfd0`. The owner-selected Winter Welcome source is Meshy task `01a20e75-2740-776c-8531-3fecd0500dbe`, SHA-256 `7e3ed20e3cb494415c07c3f85611f6fdafbc0cca53bb972206df26a57b539ffb`. All measurements use the exported model's in-place playback.

| Check | Result |
|---|---|
| Character and skin | Positions, normals and UVs for all 425,291 original vertices, the indices for all 727,442 triangles, the material objects and three embedded texture images match the confirmed source. The model has 52 skin joints, including three per finger on each hand. |
| Opening, closing and isolation | The actual separated fingers in both gloves bend and reopen. All five named isolation clips independently move the intended distal digit. The complete glove self-intersection check found zero new nonadjacent triangle crossings on either side across 687 free-hand sample rows. |
| Two-handed shaft contact | In every sampled pose, each of the ten digits retained a real surface point within **0.688 mm of the axe** or **0.822 mm of the pickaxe**. These are measured upper bounds on the true closest distance to the fitted tool triangles. Hands and shaft were evaluated from the final baked scene transforms. |
| Dynamic glove clearance | Both complete glove surfaces stayed free of new self-intersections in all 162 sample rows per strike. Combined with the six free motions, this covers 1,011 sample rows across all eight clips. |
| Strike clearance | **Zero triangle crossings across all 38 tested body, clothing and tool region pairs** on all 162 exported samples for each strike. Both same-side upper/lower sleeves clear, as do the right upper sleeve against the parka and collar, the opposing gloves, and both tools against the character's head and torso regions. Former problem intervals include axe 0.800–0.825 s and pickaxe 0.758–0.775, 1.017–1.025 and 1.108–1.242 s. |
| Contact and stance | The actual fitted tools reach the fixture in the packaged strike footage. Both boot support patches remain planted, with maximum horizontal slide **0.008 mm** across the two strokes. The lowest surface stays about 0.40–0.50 mm above the authored floor. |
| Motion and loop | The corrected shoulder trajectories avoid earlier abrupt elbow compensation. Peak upper/lower-arm angular rates are 348°/s on the axe and 406°/s on the pickaxe. Loop endpoints coincide. Both sides were checked at 120 Hz, including interpolated samples and the final encoded endpoint. |

The [review ledger](review-ledger.json) covers all eight clips, 52 skin joints and 60 joint or clothing regions. Of 1,948 checks, **1,920 passed, zero failed and 28 remain untested**. The 28 comprise 12 whole-region clearance checks plus two garment-deformation checks per strike. The unverified details include hidden face and eyewear overlap, the interiors of the cuffs and hood, and the parka, zip, pocket, hem and torso seams. The dense collision test deliberately uses spatially separated regions from the original mesh. It cannot demonstrate complete clearance at every shared seam. The matrix was verified locally against the exact GLB, clips, joints and evidence files. The skill provider did not make its stock release-check script available. [Matrix verification](matrix-verification.json)

The Godot import probe exercises all eight animations. This review covers the character asset and the two supplied fixtures. Actual Level 1 input, gameplay state transitions, mobile frame time and walking or root-motion locomotion remain outside this test. [Godot import](../../Review/Godot-Import.log)

[Finger playback](../../Review/Winter-Welcome-Finger-Motion.mp4) · [Combined tool footage](../../Review/Winter-Welcome-Tool-Motion.mp4) · [Axe contact](../../Review/Axe-Contact.jpg) · [Pickaxe contact](../../Review/Pickaxe-Contact.jpg)

[Axe, six angles](Axe_Chop.jpg) · [Pickaxe, six angles](Pickaxe_Mine.jpg) · [Glove surfaces](whole-glove-120hz.json) · [Shaft contact](baked-shaft-contact.json) · [Body and tool clearance](exported-body-clearance.json) · [Foot support](feet-tracking.json)
