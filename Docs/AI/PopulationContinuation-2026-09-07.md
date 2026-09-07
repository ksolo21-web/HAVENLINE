# HAVENLINE 0.4.2 population continuation

Date: 2026-09-07. Active project remains the Unity-free Godot 4.7.2 Android game.

## User priority

Do not fix or approve the last three custom rigs in this work order. Characters 2–4 remain the custom companions/alternate-lead roster under the existing original lead-selection rules. Their rigging fixes and final review are deferred to the final character-polish stage. All four custom GLBs, original core simulation, original gameplay contract, character textures, and motion-bake implementation are unchanged.

## Implemented

- Reusable customer pool: two male and two female base-model contracts, unique persistent visitor IDs, deterministic saved names/appearance descriptors, bounded four-person active queue, arrival/queue/departure and patience.
- Proximity-driven customer service commits one real carried unit per 0.4-second beat and credits provisional in-game supply tokens. Trades never debit the furnace/construction ledger. Existing combat takes priority. No real-money flow is introduced.
- Separate additional male/female survivors: 2.2-second proximity rescue, persistent recruitment, follow/gather/build/repair/guard jobs and conserved timed cargo. The original frozen helper remains NPC5; none of these replace C1–C4 or bypass the original opening rescue.
- Dog/cat pet archetypes: separate roster, follow/scout, threat alert cooldown and retreat, no human labor or invented cargo.
- Transactional extended saves, legacy-save migration, partial-service progress, monotonic IDs, appearance/job persistence, backup recovery, corrupt state rejection and per-template encounter seeding. One unavailable pet template does not block other ready templates.
- Actual-model-only view adapter. A template must supply an imported authored 3D model and idle/walk/run clips before runtime spawning is enabled. No primitive or custom-character clone fallback. Candidate loading does NOT approve the complete action animation set.
- Camp-menu population summary and recruit/pet assignments, scrollable content, and strict native render dimensions >=3840 by >=2160 for wide/foldable layouts. Lower-resolution review capture remains explicitly marked.

## Validation at source-preparation checkpoint

200 actual Godot checks passed locally: original gameplay 24; crew/save 52; motion/performance 46; new population 78. Headless game launch passed before the final small review refinements. Fresh post-refinement tests, launch, Mobile capture and Android export are required in the publication job. C2–C4 rig fixes were not performed; the unchanged build still generates its prior unapproved locomotion libraries.

The initial local screenshot request for Mobile Vulkan fell back to OpenGL because this container lacks the required Vulkan surface support. That capture is labeled GL compatibility, not Mobile evidence. CI must capture actual Mobile output and report its renderer. Neither environment proves physical Android 4K/60.

## Still not delivered or approved

ALL EIGHT new NPC model slots are missing. The generated names/appearance descriptors are persistent data, not visible authored hair/outfit variants. No new NPC visuals are claimed complete. A real complete frozen-rescue sequence, NPC role animations, trading counter art, environment art, wolves, production chains, connected biomes/transport, weather/audio/cloud and device acceptance remain open. Supply-token spending/economy balancing is also not implemented.

Internal source review and deterministic tests were performed; no independent AI critic was launched. The >9.0 plus all-mandatory-checks release gate remains blocked. Do not label successful export, 200 tests or empty model slots a finished game.

## Next executable production work

Create/import and review the distinct authored customer, survivor and pet models with their full role motion sets. Populate `data/npc-catalog.json` only with real assets; apply named appearance variants rather than claiming a metadata descriptor is visible. Complete and visually inspect the customer/rescue/helper loop, then keep building the original game. Preserve the deferred C2–C4 rig work for last.

## Reproduction

Run the existing `.github/workflows/havenline-godot-android.yml`. It now runs all four suites, headless launch, actual front/rear/side/three-quarter Mobile captures, native ARM64 export, APK inspection and signature verification. `tools/havenline/summarize_evidence.py` reports the new suite; the APK inspector checks both version 402 and packaged population scripts/catalog.
