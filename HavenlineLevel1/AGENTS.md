# Level 1 reference review

For every change to what players see, hear or control in this project, assign one team member as the independent reference reviewer. The reviewer works alongside the person making the change and retains the assignment through playtesting. Record both names in the handoff so the next session can pick it up.

Before editing, the reviewer and builder identify the actual GitHub design sheet for the character or object, and the relevant shot in the locked recordings. Record the source revision, path, and timestamp or view. For transfers, note the start, first arrival and end of the visible stream. For movement, measure the character's travel against body size from the gameplay camera. Label any design decision the source leaves open.

During implementation, the reviewer compares a short rendered playthrough to those source pixels, flags specific frames and checks the next iteration. Test the player's normal controls in an isolated profile. Include a full gameplay frame at normal zoom and an image at pinch zoom when judging character or prop appearance. Record which camera, resolution, device or renderer actually produced them.

Before marking a change as matching, retain the paired evidence and the independent verdict on the exact candidate. Each applicable visual or motion criterion must reach the owner's 9.5/10 threshold. Carry an open mismatch forward with its reference, affected behavior and owner. A player's report reopens the affected check. Preserve their save and keep work on the active trial branch.

Main characters and survivors share a 9.9/10 minimum for independent character art, rigging, and animation reviews. Apply any stronger gate in the registered task packet.

The original recordings and their identities are indexed in [the reference source manifest](../Docs/Design/ReferenceVideoLock/reference-video-sources.json). The [opening and upgrade clips](../Docs/Design/ReferenceVideoLock/2026-11-26-field-loop/Locked-sequences) show individual spend events.

For the Level 1 worker and pet, use the selected [male survivor turnaround](https://github.com/ksolo21-web/HAVENLINE/blob/01664a73ddf5087f17f7e159fa0b6b4ed71367b5/Docs/Design/RenderArchive/2026-11-23/selected/characters-survivors-npcs/survivor_male_01.png) and [owl turnaround](https://github.com/ksolo21-web/HAVENLINE/blob/01664a73ddf5087f17f7e159fa0b6b4ed71367b5/Docs/Design/RenderArchive/2026-11-23/selected/animal-companions/pet_owl_01.png). Compare the face, silhouette, clothing or plumage, equipment, and visible details at gameplay scale.
