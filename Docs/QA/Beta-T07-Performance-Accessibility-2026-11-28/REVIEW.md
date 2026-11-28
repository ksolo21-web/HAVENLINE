# T07 beta performance and accessibility review

The Level 1 beta starts in Ultra. At 3840×2160 it keeps 100% render scale, 4× MSAA, the authored shadow settings and the existing game assets. The graphics gear cycles Ultra, High and Low. High keeps full resolution and uses 2× MSAA with a shorter shadow distance. Low uses 75% 3D render scale and keeps the HUD at the display resolution. The graphics profiles share the same gameplay, camera and controls. [Reviewed runtime](https://github.com/ksolo21-web/HAVENLINE/commit/14db14ee243f4718fadf93f2c881869be1736025) · [Prior beta](https://github.com/ksolo21-web/HAVENLINE/commit/03d5d147b28eae4ad6f7c29eb25bf2e78e002dfa)

## Performance

Each profile rendered 18 gameplay frames from three camera positions using a 3840×2160 output window. The camp had purchased workstations and truck, an active survivor, customers and an encounter with wolves. This is renderer workload and process memory evidence from Godot OpenGL Compatibility with Mesa llvmpipe. [Measurements and method](performance.json)

| Profile | Internal 3D raster | MSAA | Peak draw calls | Peak renderer texture allocation | Sampled process memory peak |
| --- | --- | --- | ---: | ---: | ---: |
| Ultra | 3840×2160 | 4× | 729 | 1055 MiB | 2787 MiB |
| High | 3840×2160 | 2× | 730 | 929 MiB | 2715 MiB |
| Low | 2880×1620 | Off | 720 | 824 MiB | 2385 MiB |

Separate headless simulation measured up to 7.66 ms at p95 across 1,080 fixed ticks. Frame targets are 16.67 ms at 60 fps and 8.33 ms at 120 fps. The user waived physical-device validation for this beta. Sustained 4K frame rate, physical GPU timing and thermal performance remain unmeasured. [Measurements and method](performance.json)

### Proposed Ultra ceilings

Git history attributes the 650 draw-call, 1,024 MiB texture and 2,560 MiB process targets to the September 11, 2026 policy migration under the author name `havenline-integration-owner`. They were intended to reserve full-game headroom early in production. The current Ultra workload exceeded the existing global targets. [Budget commit](https://github.com/ksolo21-web/HAVENLINE/commit/e1b25edc31a290ff158eefb5e694d95cf87b4757) · [Existing ledger evaluation](existing-budget-evaluation.json)

| Metric | Existing global target | Proposed Ultra lab ceiling | Reserve in this sample |
| --- | ---: | ---: | ---: |
| Draw calls | 650 | 960 | 24.1% |
| Renderer texture allocation | 1,024 MiB | 1,408 MiB | 25.1% |
| Software process memory | 2,560 MiB | 3,584 MiB | 22.2% |

These provisional ceilings apply to beta lab planning. The main production policy and the frame time targets retain their published values. System memory observed under a software renderer includes rendering allocations and cannot establish a safe phone memory allowance. [Proposal and exact metrics](performance.json)

## Accessibility

Camp → Accessibility provides a larger HUD, reduced motion, gameplay captions and a choice of joystick side. Preferences persist separately from the camp save. The review confirmed 48 dp targets in the tested layouts, the Fold title correction, muted raid and damage cues, the reduced-motion hearth purchase, and actual touch for equipment placement and paid gate repair. The same control cycle through Ultra, High and Low passed. [Accessibility checks](accessibility.json) · [Fold at Large](screenshots/foldable_unfolded_portrait-large.jpg) · [Muted damage](screenshots/muted-damage-caption.jpg)

The accessibility safeguard passed 95 simulated-layout checks, 50 software-rendered checks and nine existing gameplay suites. The independent reviewer inspected the live captures. The tested beta supports touch and desktop movement keys. The viewport matrix emulates density and display cutouts. [Safeguard receipt](accessibility-gate.json) · [Independent review](independent-accessibility-review.md)

This package records the T07 scope reviewed here. Whole-critic 10/10 remains unassigned.
