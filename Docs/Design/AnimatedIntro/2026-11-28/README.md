# HAVENLINE — animated intro v2

Vertical animated intro for Havenline (23.5s, 720×1280, 9:16, 24 fps). This package lives on the same isolated design branch as the [hearth app icon](../../AppIcon/2026-11-27/README.md). It is an artwork delivery only: it is not wired into a Godot splash or title scene.

## Files

| Asset | Use |
|---|---|
| [havenline_intro_v2_final.mp4](havenline_intro_v2_final.mp4) | H.264/AAC master, 18,711,497 bytes, SHA-256 `88bbb21d491bf1f3304afbf42ccb5e3709c425a3b7b87828899e4f6848022d9f` |
| [havenline_intro_v2_final.ogv](havenline_intro_v2_final.ogv) | Theora/Vorbis copy for Godot 4 `VideoStreamPlayer` (`libtheora -q:v 7`, `libvorbis -q:a 5`), 19,593,157 bytes, SHA-256 `649ef58502157023744b61911c54ded221c460e34fad8be104e8abc989deb30e` |

## Shot structure

- 0–4s: camp push-in
- 4–8s: chopping
- 8–12s: log set into the wall
- 12–16s: ice wolf shatters
- 16–23.5s: family hero shot; title **HAVENLINE** and tagline **BUILD. SURVIVE. TOGETHER.** fade in from 17.5s, then fade out

Audio is loudness-normalized.

## Known limits

An independent review scored this v2 render 5/10. Hands still melt into tools in the chop, build, and wolf shots, and the small axe and glasses warp in the family shot. This file is the current delivery, not a final in-engine cinematic.

## Integration boundary

Godot 4 plays `.ogv` (Theora) natively in `VideoStreamPlayer`. The `.mp4` is the review/master copy. Do not treat presence in this folder as a hooked-up boot intro. Wire it in a later gameplay-branch build after the owner chooses the hook.
