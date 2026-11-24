# HAVENLINE current project context

User direction, 2026-09-07: continue from GitHub, build the complete Android game without Unity, preserve the original premium stylized 3D game, reject primitive art, require 4K/60 or better.

The active project is `HavenlineGodot/` on `codex/havenline-godot-android`, based on `agent/havenline-production-art-gate` (`7cee199`). Historical Unity source is retained for provenance and is excluded from the native Godot build. No Unity tool or license is needed.

The full gameplay source was recovered from `ksolo21-web/Hummer`, branch `havenline-unity-reference-rebuild`, commit `1ba652af21f4c06229aa94ed2ab1c48f94c9b094`. Its reference contract 1.3.1 is retained verbatim in `data/reference-contract.json`. Engine-specific historical fields in that file are provenance, not the active build configuration. `HistoricalGameplayLock.md` records the original design; this document supersedes its Unity-only statements because the user explicitly changed engines.

Preserve landscape, close orthographic camera; C1/C2 selectable leads with the other lead plus C3/C4 active; uncapped logical inventory; automatically gather/fight/rescue/deposit/build/repair by proximity; furnace L2 at 18 wood AND 6 stone; warmth 4.5 to 8; 2.2-second rescue; north barricade at 8 wood AND 3 stone; wave gated on all three prerequisites, first delay 48 seconds and three wolves. The rescued survivor is an additional NPC. No manual action buttons. The reference video is https://youtube.com/shorts/JicjHsoUj68.

Character1 uses the exact supplied `Character-Rig-Fixed-1.glb`. Characters2–4 use recovered V7 staging files with the identities/hashes documented in historical context. They remain candidates, not approved production assets. Preserve original geometry, skinning, UVs and textures. Import/render validation does not grant whole-rig, locomotion, combat/gather animation, or human style approval.

Production scope also includes additional helpers/jobs, processing chains, persistent connected biomes (frozen, forest, desert, underwater, sky, volcanic, swamp, ruins, underground, alien), vehicles/connectors, weather/day/night, and verified Google identity/cloud saves. Do not claim those features are complete when they are only planned or represented by configuration.

Release remains blocked until all production features, authored visuals, complete motion sets and independent rig reviews, Android lifecycle, authentication/cloud integration, and sustained 4K/60 physical-device tests pass. Record actual evidence; never invent a score. Development APKs must use an isolated package and be labeled honestly. Do not weaken release gates to get an APK.
