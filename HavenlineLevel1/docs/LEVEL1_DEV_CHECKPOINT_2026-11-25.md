# Havenline Level 1 development checkpoint · 2026-11-25

This is a development record, not a gameplay release. The playable code is unchanged by this checkpoint. Open `HavenlineLevel1/previews/integrated_opening.tscn` from the dedicated Level 1 replacement project. It does not contain the full Level 1 loop.

## Playable baseline

[11c14a1c](https://github.com/ksolo21-web/HAVENLINE/commit/11c14a1c41971067c7dc97db69375f720a408f68): the revised snowy opening, harvestable starter tree, paid camp, centered furnace and two working gates. After three chops and the completed fall, the tree disappears and regrows in five game seconds. Repeat chopping does not duplicate the one-time starter wood. Historical PR #101 footage is not proof for this build.

## Work in review, not active in gameplay

| Work | Verified so far | What must pass next |
| --- | --- | --- |
| Character 1, first priority | The boot repair trials did not yield a usable walk. One test pose achieves real left heel contact, but the right toe remains 11.57 mm above ground in the same pose. No replacement walk, run or two-handed chop was exported. | Author a coherent stride and check both boots across a full cycle. Check the two-handed grip and chop separately. Require independent multi-angle review, with no identity or scale change. |
| North-fence customer counter | A 3.65 m center section fits without moving the furnace or gates. A temporary collision fixture passed 66/66 builder and independent Godot checks: the player can cross both gates in both directions, but cannot cross the counter midpoint or seams. The archived counter is not approved for gameplay; its stock and payment markers are about 22 cm above the physical top and cannot be used as object resting points as-is. | Mount the actual reviewed counter with solid fence joins, distinct interaction and item-rest points, and test real player and customer approaches. The temporary barrier does not establish a third gate, art approval or functioning customer service. |
| Buy plot and camera | The larger 1.40 m graphic in the private candidate keeps the original 0.72 m charge range: a funded player at its wider edge did not pay; at the original range they paid once. The first camera angle rotated the world view away from the existing directional controls. The revised candidate keeps the original horizontal heading and lifts the view; source alignment was independently checked, not yet native movement or rendered readability. | Verify actual directions and payment regressions, then capture the price on ordinary approaches at phone-sized framing. Preserve the existing plot art, original purchase range and no floating substitute. |
| First enemy animal | Required for Level 1. The baseline provides a dry field route. No approved runtime animal actor or encounter is installed. Static enemy references are not mesh, rig or gameplay approval. | Connect a reviewed enemy-animal asset and test a real encounter from ordinary movement. Do not substitute companions or later human invaders. Fishing is outside Level 1 and must not be a dependency for service or level completion. |

Only independently reviewed, playable changes should alter the gameplay baseline. The test evidence above does not establish full Level 1 completion, native phone performance, or a Level 2 unlock.
