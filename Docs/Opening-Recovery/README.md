# Level 1 opening recovery checkpoint — 2026-11-23

**Status: documentation and standalone QA code only. Not a playable build, not a release.** The branch is based on the default tree only to preserve Git history; do not launch that tree as the new opening.

| Work | Verified state |
| --- | --- |
| Old playable Godot baseline | [PR #101 source and scene](https://github.com/ksolo21-web/HAVENLINE/tree/5abfc29f1c3c51bef99247641cf1131581899942/HavenlineGodot). Historical only. The earlier footage starts with a visible Heat 1 furnace, preplaced equipment, red camp ground, paths, and six entrances. Do not count it as evidence for the revised opening. |
| Revised Level 1 furnace | Original mesh recovered and byte-verified: GLB SHA-256 `35d5529066168834ed87c09e0db6f98bf058f5a75b0175c57e0e78bbc2a70f5a`, 856,696 triangles. It is a source master, not the runtime asset; binary not included in this commit. |
| Compact camp, timber fence and revised gates | Earlier isolated source and test findings exist, but the exact newer packages are not yet recovered. Not installed together in any verified branch. |
| Audio build QA | [Offline WAV validator and its eleven synthetic tests](qa/audio-readback-v2/README.md) are committed as source. This does not certify real generated audio, listening quality, engine import or playability. |

## Gates for the next runnable checkpoint

- Start from the pinned Godot project or a separately verified newer project tree. Record the exact commit and scene before capturing.
- Start with no free furnace, fence, equipment, or companions. Use ordinary play to earn and finish the Level 1 purchase. Show the centered furnace and fence appear after commitment, with two usable gates. Use compact camp ground without a red floor; keep uninterrupted snow outside the camp, with no painted or carved paths.
- Show ordinary movement through both gates in each direction. A physics control, standalone render or asset file is not the same as a played opening.
- On an isolated save, verify per-node identity and respawn, not just total stone. Swapping the world locations of two stones whose identifiers are assigned by list order can preserve the total but restore depletion on the wrong mesh. Test an asymmetric pair and reject incompatible saves without touching a real profile.
- Keep payment pads visible during use and through the final material transfer. Verify the correct receiver, matching typed quantity and no duplicate debit or effect on reload.
- Record actual validation, unresolved limits, and the exact link in each checkpoint. Never label an isolated component a playable build.

No workflow, release, live profile, default-branch or production deployment changes are part of this checkpoint.
