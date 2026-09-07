# Havenline 0.4.4 — environment-only acceptance

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

## Required review evidence
Actual Godot Mobile renders: normal gameplay front, rear, left, right,
three-quarter, night, blizzard, warmth4 overhead, gathering, shelter front/rear,
furnace detail, tree detail, and a native >=3840x2160 render at scale 1.0.
Check full images and detail crops, not only a contact sheet. Compare the prior
0.4.3 output. The normal scene must keep the crew readable and show both shelters.
Examine roof lips, snow/rock joins, bark, normals, leaf silhouettes, material
contrast, light leaks, near-plane cuts, terrain contact, and camera transitions.

## Scoring
Score each dimension 0–10: silhouette/craft, material/style fidelity,
lighting/readability, composition/camera, geometric integrity, and actual-output
verification. The lowest dimension is the overall result. Target 10; acceptance
requires STRICTLY >9 and no mandatory defect. Averages cannot hide a defect.
Give evidence filenames and concrete reasons. Do not grant a score without
opening actual image evidence. If image review is unavailable, mark UNREVIEWED.
A code review alone does not certify visual quality. Automated geometry checks
and successful export are not a visual critic. Never label builder self-review
as independently executed review.

This is an environment-art gate, not whole-game completion. Sustained physical
Android native 4K/60, thermals, touch/fold lifecycle, missing NPC art and gameplay,
audio completion and cloud saves remain separate unapproved production gates.
