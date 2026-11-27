# Havenline Beta T01 · Forest traversal and harvesting

The foundation is signed Android Build 16. Its gameplay source is `92fa91760a45eea306d7bda4da4b705b51b6f103`, and the trial branch recorded it at `429cb7ea56d98f7d023d7d6eeb18c89feb711fbc`. Build 16 pricing, inventory receipts, and save schema are carried forward.

## Playable changes

- The forest keeps its existing placement and the cool layered conifers used in the opening. Foreground crowns open a small local window around the player and survivor, including near their boots. The trunks and their cutting surfaces stay available.
- The survivor can select any reachable valid tree or bank that the field can load. Survivor movement can stream its own grove and hold its current job while the player walks elsewhere. When the live tree set has no usable job, it checks standing batched trees in small batches. A depleted tree remains unavailable until it regrows.
- The truck's two disks share a continuous cutting envelope. The center can chop, mine, and damage enemies. Side reach, repeated-hit cooldown, and camp protection are preserved.
- The guard alone uses the see-through treatment. A cached half-resolution render of the tower meshes identifies where opaque tower parts hide the guard. The original tower materials use ordinary scene lighting.

## Source and visual checks

Independent review used the locked opening forest at B 0–6 seconds, the selected GitHub forest-lake concept, and the verified native gameplay camera. The same original sources are included in the reference record. The tower and truck follow their latest selected Havenline sheets and exact imported game assets.

The Meshy comparison tree was generated from a pine isolated from the selected forest-lake sheet. This 2,379-triangle pilot matches the concept's green foliage and rounded snow deposits. Its single combined surface and green palette require additional preparation for the cool opening forest and independent trunk contact. The pilot is available for comparison alongside the opening pines. [Meshy provenance](Meshy/Provenance.json) · [Normal preview](Meshy/Pine-comparison-front.jpg) · [Three-quarter preview](Meshy/Pine-comparison-quarter.jpg)

This is the start of Beta T01. Full T01 reference and physical performance approval remains open. The 9.9/10 requirement applies to main-character and survivor reviews. The existing rig scores do not qualify under the new threshold, and this patch does not award a new rig grade.

[GitHub T01 reference matrix](https://github.com/ksolo21-web/HAVENLINE/blob/a4e643aeb563b6f9cfda8b840c0651d13326eec8/Docs/Production/ReferenceRefresh/2026-11-27/TASK_REFERENCE_MATRIX_T01_T80.md#t01) · [Selected forest-lake sheet](https://github.com/ksolo21-web/HAVENLINE/blob/a868ae89cdf2f120b478aa0a48fff35e09cc465c/Docs/Design/MissingRenderCoverage/2026-11-27/coverage-completion-01/selected/world-biomes-forest-lake.png)

## Review results

Nine focused native suites passed. The independent player routes reached all 24 tested waypoints and recovered the same pine after its five-second regrowth. The separated survivor case kept an active tree while the player moved 110 metres away, with 10 chunks live. The center blade checks verified pine, rock and wolf contacts, preserved the side disks and rejected duplicate or out-of-range contacts.

The scoped canopy review measured 9.6/10 for readability and 9.4/10 for forest framing. The scoped guard view measured 9.5/10 and recorded one changed edge pixel in one 1× frame. Those results give concrete repair targets for the later full reference and device review.

[Independent forest review](Review/Independent-T01-review.md) · [Independent guard review](GuardReview/FinalCandidate/README.md) · [Native tests](Verification/Native-status.json) · [Meshy in the forest at 2×](Meshy/In-field-Meshy-2x.jpg)
