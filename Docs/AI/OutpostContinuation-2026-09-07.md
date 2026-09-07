# Havenline 0.4.3 outpost continuation

Source-preparation checkpoint, September 7, 2026. Development only, not production approval.

## Implemented this iteration
The existing native Godot game now has a saved simulation-time clock, blended clear/flurry/snowfall/blizzard/clearing weather, daylight and moonlight, bounded instanced snowfall, a continuous sculpted terrain surface, and an expanding furnace-thaw boundary tied to the original gameplay warmth radius. Cooling responds to weather; clear daytime preserves the original cooling rate. Pausing stops weather and thaw progression, with no offline time debt. Legacy saves acquire the extension transactionally and invalid extensions use the existing validated recovery backup.

Actual gathering/deposit/build/rescue action timers drive the contextual indicator. The existing movement-only controls are unchanged. Compact clock/weather/warmth/health text and upgrade feedback are integrated into the real scene. Six deterministic original procedural audio clips add wind, furnace, wood, stone, transfer and upgrade feedback. Sound has a persisted mute setting, pause handling and bounded polyphony. This is not the finished soundtrack or full action Foley; no listening-quality certification is claimed.

`python3 tools/havenline/bake_outpost_audio.py` must run BEFORE Godot import. The script, generated manifest and deterministic source preserve provenance. Existing `res://tools/bake_crew_motion.gd` is unchanged and only recreates prior candidate locomotion libraries.

## Verification and limits
Six engine suites total 311 checks at this checkpoint. Twenty-three new actual-scene tests exercise touch movement, menu/application pause, no resumed time debt, restored sound preference, bounded sound voices and visual warmth interpolation. Local screenshots use software OpenGL Compatibility, NOT Mobile Vulkan or physical Android. Android build and Mobile capture outcomes must be read from the subsequent CI artifacts, never inferred from this checkpoint. The normal review workflow includes daylight front/rear/side/three-quarter views, night, blizzard, level-four overhead, gathering, and a separate native 3840x2160-or-greater capture. QA scenarios are declared fixtures, not claims that an unimplemented rescue/combat progression is playable.

## Preserved hard requirements / next critical work
All original custom GLBs remain unchanged. C2-C4 rigging corrections and final reviews stay last. All thirteen distinct NPC model slots remain empty (four customers, two additional human survivors, seven animals). The roster remains dog, lion, tiger, bear, wolf, owl, fox, with no domestic cats; prior migration is preserved. Missing art cannot create invisible working actors. The supplied animal PNGs remain concept references, not finished rigs.

The environment remains below Kaleb's finished non-primitive visual standard, especially tiered/repetitive trees, exposed foreground undersides and simple structures. The complete visible rescue/combat loop, authored NPCs and role animation, production chains, connected biomes/transport, full audio, cloud identity/saves and physical Android lifecycle/thermal/native-4K60 evidence remain release blockers. No independent critic was executed and no >9 score is assigned.

Continue actual construction and rendered review. Show progress bars in commentary BEFORE substantial work and update them during execution, not only in the final response. Passing remains strictly >9 with every mandatory gate verified; preserve failures and do not relabel internal review as independent.
