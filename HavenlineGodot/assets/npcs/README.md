# Havenline NPC model contracts

No placeholder or core-character substitute is installed here. `data/npc-catalog.json` records eight distinct model slots: two male and two female customer bases, an additional male and female survivor base, a dog and a cat. These slots are NOT finished art.

Models must be authored, textured and skinned premium stylized assets, with idle/walk/run and role-specific complete animation. Customers need waiting, interaction and departure; survivors need rescue, carry, gather, build, repair, combat and reactions; pets need species-correct locomotion, sit/rest and alert.

Each template needs real-angle/render/whole-cycle review and >9.0 plus every mandatory gate passed. Customer reuse is permitted; core character reuse as random NPCs is not. Variant slots (palette/hair/outfit) are persistent descriptors until an authored model provides matching named parts. No nonexistent variation should be claimed visible.

Set `asset_status` to `candidate` only after placing and inspecting an actual `.glb`; production approval is a separate gate. The renderer does not construct primitive stand-ins.
