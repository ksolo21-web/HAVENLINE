# Havenline 0.4.5 — environment-only acceptance

Highest priority: replace the rejected primitive-looking outpost, not new gameplay.
Four custom GLBs remain unchanged; C2–C4 rig repair/review stays last. Missing NPC
models remain explicitly missing. No Unity build or runtime is introduced.

## Actual work to inspect
- `tools/havenline/bake_environment.py`: 14 deterministic replacement GLBs;
  branching conifers, snowy timber shelters, furnace, storage, barricades,
  resource rocks and log, ground boulders, shrubs and lanterns.
- `scripts/main.gd`: new asset routing, individual tree cutaway, close-camera
  look-ahead and safe near plane. Do not confuse QA closeups with normal framing.
- `outpost_surface.gd`, `outpost_snow.gdshader`, `outpost_view.gd`: shared snowbank
  heights, trampled trails, furnace thaw, normal detail and depth-based weather fog.
- `evergreen.gdshader`: actual Mobile-compatible dither cutaway, not unsupported
  GeometryInstance3D.transparency. Tree nodes/resource state must remain intact.
- `device_benchmark.gd`, `performance_record.gd`: actual frame interval sampling
  and a visible 30-minute measurement UI. These do not certify display presentation.

## Required review evidence
Actual Godot Mobile renders: normal gameplay front, rear, left, right,
three-quarter, night, blizzard, warmth4 overhead, gathering, shelter front/rear,
furnace detail, tree detail, and a native >=3840x2160 render at scale 1.0.
Check full images and detail crops, not only a contact sheet. Compare the prior
0.4.3 and 0.4.4 output. The normal scene must keep the crew readable and show both shelters.
Examine roof lips, snow/rock joins, bark, normals, leaf silhouettes, material
contrast, light leaks, near-plane cuts, terrain contact, and camera transitions.

## Scoring — user escalation on September 7, 2026
Score each dimension 0–10: silhouette/craft, material/style fidelity,
lighting/readability, composition/camera, geometric integrity, and actual-output
verification. The lowest dimension is the overall result. Acceptance now requires
EXACTLY 10/10 in every mandatory dimension and view, with no known mandatory defect.
This supersedes the earlier >9 threshold for the current environment task.
Averages, rounding and repeated scoring without a verified improvement cannot hide a defect.
Give evidence filenames and concrete reasons. Do not grant a score without
opening actual image evidence. If image review is unavailable, mark UNREVIEWED.
A code review alone does not certify visual quality. Automated geometry checks
and successful export are not a visual critic. Never label builder self-review
as independently executed review. Preserve invalid/failed reviews and raw model output;
invalid, unsupported or low-confidence findings require verification, never automatic approval.

## Separate native Android performance gate
Require actual internal width >=3840 and height >=2160, render scale 1.0, at sustained
>=60 FPS on a named physical Android target during a representative 30-minute run.
Verify presented-frame pacing, thermals, lifecycle and resolution throughout the run.
Do not substitute fixed-fps screenshots, averaged counters, Linux software rendering,
upscaling, or a quiet scene without the completed game's load for this requirement.

This is an environment-art gate, not whole-game completion. Physical Android 4K/60,
thermals, touch/fold lifecycle, missing NPC art and gameplay, audio completion and
cloud saves remain separate unapproved production gates until actually verified.
