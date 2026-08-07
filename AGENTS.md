# HAVENLINE Agent Instructions

Before substantial HAVENLINE work, read `Docs/AI/UnityProjectContext.md` and inspect the current repository state for anything newer.

## Core execution rule

**Work through failures and blockers. Do not get stuck.** Diagnose failures, preserve good work, use alternate approaches or fallbacks, reject worse experiments, and keep progressing until reasonable paths are exhausted. Never fabricate a pass or claim unverified work is complete.

## Project rules

- Shipping gameplay is landscape-only.
- Preserve working architecture and assets unless a change is justified and validated.
- Character 1 and Character 2 are the playable lead choices; the unselected lead becomes a helper/companion alongside Characters 3 and 4.
- Do not approve character assets from GLB/static inspection alone. Require the Unity/URP, pose/clipping, gameplay-scale, and human side-by-side gates documented in `Docs/AI/UnityProjectContext.md`.
- Do not silently fall back to an older character checkpoint when a newer proven one exists.
- Repository evidence is authoritative when chat memory and repository state disagree.
