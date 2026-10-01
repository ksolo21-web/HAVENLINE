# T04 frozen scope — reference camera and automatic screen composition

## Required outcome

The shipping camera must preserve Havenline's close, oblique,
near-orthographic reference presentation while composing the selected lead,
immediate action space and relevant nearby target automatically across the
required landscape phone, tablet and foldable aspect ratios.

T04 must keep actor/item scale readable relative to the shorter screen
dimension. It may reveal additional world on wider displays, but may not
stretch the scene, crop away the active interaction, or zoom so far out that
gameplay becomes a distant diagram.

## Required behavior

- Keep the selected lead as the stable visual anchor.
- Use movement/facing look-ahead rather than a permanent world-direction bias.
- Include a valid nearby contextual target without snapping or oscillating.
- Preserve the reference contract's orthographic baseline, three-quarter
  viewing direction, near-plane safety and foreground-cutaway compatibility.
- Adapt composition automatically for the landscape device matrix, including
  resize and fold transitions; no manual device or camera selector.
- Remain deterministic, finite and bounded when velocity, target or viewport
  inputs are absent or invalid.
- Add no geometry, textures, physics bodies, animations or gameplay controls.

## Explicit exclusions

- No environment, fence, river, station, character, animation, HUD, economy,
  save-schema or gameplay-system redesign.
- No T05+ content, photo mode, manual pan/zoom, camera shake or cinematic
  sequence system.
- No change to the authoritative reference contract values.
- No claim of physical-device 4K/60 certification; that remains T68/T69.

## Ownership and wiring

The isolated builder owns `@reservation:T04`. Shipping integration requires a
minimal call site in `HavenlineGodot/scripts/main.gd`, which is integration-only.
The builder must submit a structured change request; only the integration owner
may apply that wiring after the isolated candidate passes ownership review.

## Acceptance evidence

- Exact-source gameplay frames for 16:9, 20:9, 16:10, 4:3, foldable outer and
  foldable inner landscape states.
- Motion samples showing stable follow, directional look-ahead, target
  inclusion, target release and resize/fold transition behavior.
- Reference pixels shown alongside normal gameplay-scale candidate frames.
- Screen-space measurements for actor scale, lead anchor, target visibility,
  HUD-safe composition and cross-aspect consistency.
- T01–T03 impacted regression, deterministic camera tests and C1+C2+C6 review.
- Every mandatory score strictly greater than 9.0, with target 10/10 and no
  unresolved mandatory defect.

