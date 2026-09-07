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
