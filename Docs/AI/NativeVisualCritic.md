# Native visual and motion acceptance gate

A passing build is not a passing visual review. Production acceptance requires at least 9/10, with 10/10 as the goal, and every critical check below passing. A missing critical item means NOT ACCEPTED regardless of an average score. Do not invent an independent agent, score, screenshot, device test or approval.

## Required evidence

Inspect real renderer output from the exact candidate source/assets: front, rear, both sides and the gameplay camera; full idle/walk/run loops; gather, pickup, carry, deposit, rescue, building, repairs, attacks and impacts. Inspect all four characters separately and together. Record renderer, render resolution, source commit, source asset hashes and test phase. Review in slow motion as well as normal speed. A still image cannot certify locomotion.

## Critical motion and art checks

- Exact character identities, readable silhouette and face/clothing/accessory preservation.
- No T/rest-pose stand-ins in motion. No bone stretching, inverted joints, detached hands, broken shoulders, inward-collapsing knees, floating feet or flat-footed running substituted for proper toe-off and heel recovery.
- Ground contact, foot roll/toe bend, stride-speed matching, planted-foot slip, turns, transitions and stop/start behavior.
- Garment, hair, straps, kneepads, fasteners, backpacks and carried-item contact throughout the motion, including intersections and underside/rear views.
- Visible synchronized action anticipation, impact, recoil, tool grip and resource transfers. An idle pose next to a changing inventory is not complete action animation.
- Authored premium stylized environment and prop forms/materials, not primitive blockouts disguised by export format or high polygon counts.
- Readable cold/warm hierarchy, shadow grounding, no clipped highlights hiding detail, no broken seams or overlapping foliage/structures that obscure the lead.
- Real rendered rescue and threat encounters. No invisible damage, invisible workers, missing targets or fake completion flags.
- Landscape phone/fold framing, touch safe areas and readable contextual UI without permanent action-button clutter.

## Performance acceptance is separate

Require an identified physical device and exact APK/renderer/settings, sustained actual-gameplay sampling including busy scenes and warm thermal state, lifecycle/fold interruptions, native internal resolution evidence and display/frame-time evidence. Lower-resolution software previews, average FPS, configured render size or GPU-free headless tests cannot pass this gate.

Current 0.4.1 decision: NOT ACCEPTED for production. Locomotion transfer and technical tests are development evidence only. No whole-rig score or physical-performance certification is issued.
