# HAVENLINE Agent Instructions

Before substantial HAVENLINE work, read `Docs/AI/HavenlineProjectContext.md` and inspect the current repository state for anything newer. `Docs/AI/UnityProjectContext.md` is historical context.

## Core execution rule

**Work through failures and blockers. Do not get stuck.** Diagnose failures, preserve good work, use alternate approaches or fallbacks, reject worse experiments, and keep progressing until reasonable paths are exhausted. Never fabricate a pass or claim unverified work is complete.

## Project rules

- Shipping gameplay is landscape-only.
- Preserve working architecture and assets unless a change is justified and validated.
- Character 1 and Character 2 are the playable lead choices; the unselected lead becomes a helper/companion alongside Characters 3 and 4.
- The user explicitly retired Unity on 2026-09-07. The active Android project is `HavenlineGodot/`, using Godot 4.7.2. No Unity installation, license, runtime, or build step is allowed in this path.
- Do not approve character assets from GLB/static inspection alone. Require actual Godot renderer, whole-rig animation/clipping, gameplay-scale, and human side-by-side evidence. Preserve the quality requirements when changing engines.
- Keep the original gameplay contract, four distinct crew identities, unlimited carrying, proximity actions, and landscape camera. No primitive/blockout art may be presented as production art.
- 4K/60 is an acceptance requirement, not a marketing claim. Actual internal resolution, frame intervals, sustained physical-device evidence, and temperature/lifecycle behavior must pass. Never silently lower render resolution or count upscaling as native 4K.
- Do not silently fall back to an older character checkpoint when a newer proven one exists.
- Repository evidence is authoritative when chat memory and repository state disagree.

## Population continuation — September 7, 2026

- Custom Characters 2–4 keep their existing identities and files. Defer their rigging fixes and final rig review to the final character-polish stage; this is not approval.
- Customers are a distinct reusable pool (two male and two female model slots). Additional male/female survivors and pet companions have separate models and persistent identities, not copies of the custom crew.
- Missing authored NPC models must never spawn invisible working actors or primitive stand-ins. `data/npc-catalog.json` tracks actual model readiness separately from gameplay tests.
- Use the saved planner/critic workflow and show truthful milestone bars during substantial work. Passing requires strictly >9.0 AND every mandatory check; internal review and automated tests are not independent critic execution.

## Animal roster and progress-display correction

- Animal companions are exactly dogs, lions, tigers, bears, wolves, owls and foxes. No domestic cats. The retired cat ID exists only in explicit legacy-save migration and rejection tests.
- Use the seven user-provided references registered in `Docs/Art/AnimalCompanions/reference-register.json`; do not replace their premium stylized expedition look with primitive stand-ins. Reference images are not rigged models or in-game render evidence.
- Legacy cat saves migrate to foxes without losing identity, recruitment, assignments or partial rescue progress. The expanded encounter pool must remain restart-safe and fail-closed for missing art.
- Show the first explicit progress bar in COMMENTARY BEFORE substantial tool work, then update it during work at verified milestones. A completed bar buried in the final answer alone does not meet the user's requirement. Include completed/total milestones, current stage, verified result and next action/blocker; never present iteration progress as whole-game completion.
- C2-C4 rigging fixes and final review still stay last. This roster correction does not approve their existing rigs or the unfinished animal models.
