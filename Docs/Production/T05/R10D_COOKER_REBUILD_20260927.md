# T05 R10D cooker rebuild checkpoint

Status: ACTIVE; T05 visual approval remains blocked.

Primary Havenline authority: 18607.png (Levels 1-25 Early Camp Upgrade Set). Continuity: 18609.png. Late-game polish ceiling: 18608.png.

Starting materialized source: 5fe99a5288b7822c37226f431cf22d5e62ba8189.

Observed exact-source R10C defect: actual Godot review pixels showed cooker_processor dominated by a generic smooth tank/vessel silhouette on a timber frame. The side view remained visibly primitive relative to 18607 cookfire, butcher-table and assistance-machine construction language.

R10D bounded repair:
- cooker_processor only;
- replace dominant tank silhouette with constructed timber chassis + work deck + fabricated stove core + recessed hot chamber + prep surface + cookware + offset banded flue + service wheel + irregular snow;
- preserve asset ID, footprint, sockets, material ceiling, arrangement and gameplay contract;
- triangles 4016 -> 4988;
- total kit 92860 -> 93832, still below 180000;
- camp batch unchanged at 55912;
- lakeshore batch 34080 -> 35052.

Local exact replay evidence before persistence:
- deterministic source-integrity suite passed;
- Godot T05 station/prop suite passed with zero failures;
- cooker footprint X/Z, terrain seating, sockets, lakeshore route/crossing/movement checks all passed;
- isolated OpenGL llvmpipe 1280x720 multi-view review shows materially improved purpose/silhouette;
- render path is fallback review evidence only, not Vulkan/native4K/shipping-main acceptance;
- no independent critic has run; no >9 score is claimed; task_approved remains false.

Next open visual work: materialize R10D in-repo, run exact-source Vulkan/native render evidence, then audit the still-weaker intake_machine/conveyor_straight presentation and full family gallery before any T05 closure.
