# Havenline animal-roster correction — 2026-09-07

## Requested correction
Animal companions are dogs, lions, tigers, bears, wolves, owls and foxes. Domestic cats are removed. The seven user-supplied expedition-animal images are the design references. They are not GLBs, rigged models, animation evidence or in-game screenshots.

Progress updates belong in commentary before substantial work and at verified milestones during execution, not solely as a completed bar in the final response. Custom Characters 2–4 rigging fixes and final visual reviews remain deferred until last.

## Implemented source changes
- Seven separate animal archetypes; four customer and two human-survivor archetypes preserved (13 total required NPC models).
- Nine staged encounter sites (two human survivors and seven animals), with per-template missing-art gating and duplicate-safe seeding.
- Schema-1 cat records and their site identifiers migrate to foxes. Persistent identity, name, recruitment, assignment, alert cooldown and partial rescue progress are retained.
- Existing four-site saves can acquire the five additional sites without duplicating the old dog/fox or human encounters.
- Current-schema cat injection, mismatched legacy species, orphan site identifiers, fractional/string/bool version tags and unsupported revisions are rejected transactionally.
- Numeric version checks accept integral JSON numbers without weakening validation. Three initially failing save/recovery tests were fixed and the full suite rerun.
- An avian production profile is recorded for the owl. Authored flight, takeoff/landing, wing clearance and aerial navigation are still unfinished; this metadata does not implement them.

## Actual validation
Pinned Godot 4.7.2.stable.official.ed1daf0bf imported the project successfully. Four suites passed: original simulation 24, crew/persistence 52, motion/performance 46, population 112 — **234 checks total**, including 34 additions over the previous 200-check suite.

The unchanged build generator recreated the existing derived locomotion libraries only to run regressions. It was not a new rigging fix or whole-cycle visual review. All four original character GLBs match the prior source archive byte-for-byte. All seven reference PNG copies match the original uploads byte-for-byte.

The first test attempt and final test logs are retained in the downloadable evidence package. Automated checks are not a separately executing AI critic. No independent critic has run and no visual quality score is assigned.

## Scope and remaining work
All 13 authored NPC model slots remain empty. No new rendered animal, animal animation, environment improvement, sustained physical Android 4K/60 proof or finished-game approval is claimed. This correction is a source update; no replacement APK was produced locally. The previous 0.4.2 APK does not contain this correction.

Original PNG files are included under `Docs/Art/AnimalCompanions/` in the downloadable source bundle. The repository reference register identifies their filenames and checksums; it does not falsely claim the PNGs themselves were uploaded to GitHub.
