# Havenline Beta T04 gameplay camera

The fixed oblique orthographic camera follows the character's actual ground movement and frames the current nearby interaction. The camera can translate along the ground as the player moves. Its authored angle, 13 m short-axis span at normal zoom, and 2× pinch range remain authoritative. The responsive portrait and landscape playtest layout adapts automatically, including the Fold cover, inner display and rotated counterparts. Wider displays show more terrain.

The camera checks the actual screen rectangles of the objective, health and resources, settings, and bottom controls. At a real service position the player, counter, order bubble and all three customers fit at both zoom levels in the eight tested layouts. The active build plot uses the visible outline of its purchase pad. Camera tracking follows the motion observed each frame and settles after input or a local action ends. Continuous tracking moves at most 0.175 m per 60 Hz physics step, including when an interaction enters or leaves the frame.

## Verification

- The exact camera suite passed all 71 checks, including actual pinch input, resized touch ownership, playable actor scale, plot visibility, the live paying queue, and invalid updates.
- Native software captures cover eight desktop-simulated phone, tablet and Fold dimensions. The 3840 × 2160 gameplay captures use render scale 1.0 at both 1× and 2×. Independent tests repeated real touch runs in both directions and the south and east gate approaches.
- The moving lead and resting body retain their fixed proportions. The nominal lead projects to about 10.29% of the screen's short edge at 1× and 20.58% at 2× across the matrix. In the matched two-direction run the player travels 7.74 m at 6.25 m/s. Camera framing places visible room ahead where the old camera trailed the actor.
- The HUD suite's meal-count assertion also fails on the T03 baseline. The complete standalone suite output is identical on both sources. The camera feature gate and the inherited gameplay coverage are recorded in the test results.
- Headless camera-solve averages range from approximately 0.16 to 1.31 ms in the repeated test scene while the renderer and regression tests also ran. This is solver timing measured separately from native frame rendering. Physical hardware and sustained performance testing were skipped for the current playtest.

The selected GitHub Character 1 and camp HUD sheets and available locked footage bind the independent review. The later RF02 18–22 second footage was documented in the reference registry. Its original pixels were unavailable for this run.

[Candidate source](Candidate.json) · [Fold inner service at 2×](Capture/Inner-queue-2x.jpg) · [Native 4K at 2×](Capture/4K-queue-2x.jpg) · [Reference board](Reference/Locked-and-Build11-context.jpg)

The independent reviewer assigned 10/10 to each scoped reference and technical visual dimension and to the camera tracking and gate transitions. The final source passed 15 of 16 regression suites. The inherited HUD result reproduced byte for byte on T03.

[Independent review](Review/Exact-186be990-review.md) · [Touch movement replay](Capture/Camera-movement.mp4) · [Complete regression report](Tests/Suites.txt)
