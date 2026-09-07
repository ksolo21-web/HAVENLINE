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

## Universal planner, critic and progress standard — 2026-09-07

Read `Docs/AI/UniversalWorkStandard.md` and `Docs/AI/HavenlinePlanner.md` before substantial execution. Preserve every original contract requirement and stronger project-specific rule.

Use Planner -> Builder -> Independent Critic -> Fix -> Retest. Custom agent definitions are `.codex/agents/kaleb_planner.toml` and `.codex/agents/kaleb_critic.toml`; the portable skill is `.agents/skills/kaleb-quality-loop/SKILL.md`. Launch them only through an actual available agent runtime; record real run references. Definitions, self-review and Python validators are not separately executed agents. When spawning is unavailable, keep the independent-review gate blocked while advancing useful work.

Passing is strictly **greater than 9.0/10**, with **10/10 the target**. This supersedes historical >8 and >=9 thresholds, including legacy `at_least_9` status labels. Every mandatory criterion and required evidence must pass; the weakest mandatory dimension sets the release score. No unresolved major/blocking defect or untested mandatory requirement may be hidden by an average.

Require actual rendered multi-angle/gameplay/close-up captures and whole animation cycles/transitions. Never approve from generated illustrations, static imports or software screenshots as device-performance proof. Preserve independent human approval gates.

Show concise user-visible progress commentary during substantial work, generally around every 15 seconds or 2-3 tool calls when possible and subject to tool restrictions. Use named stages and actual verified/required counts, not invented time-driven percentages. Do not claim app-level UI modifications, control of other running chats, or background activity that has not actually been scheduled. Preserve a reproducible checkpoint with exact revision, evidence, defects, remaining work and next action.
