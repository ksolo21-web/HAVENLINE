# T05 R10T rendered-defect repair checkpoint — 2026-09-27

Status: **ACTIVE / NOT APPROVED**

## Source and visual authority
- Parent exact source: `efc0d66dff20411084a86954dc9aaf70f92ee8cb`.
- This commit adds the user-supplied `18600.png` winter asset sheet and `18607.png` Levels 1–25 early-camp board to the durable T05 visual authority.
- Furnace R01 remains preserved because fresh comparison did not expose a concrete furnace regression.

## Actual rendered defect findings
Internal visual review used actual Godot 4.7.2 captures from the current T05 kit. The local machine lacked the pinned Vulkan ICD, so the review used the OpenGL compatibility renderer only as a defect-finding fallback, never as final visual approval.

The 12-frame quick-look exposed three concrete defects:
1. `service_counter` still read too much like a pale generic table at representative reverse/gameplay distance.
2. `defense_platform` still read as an exposed scaffold and its upper silhouette lacked the authored watchtower language in the newest Havenline renders.
3. `service_counter`, `processing_counter`, `defense_platform`, `fishing_rack`, and `cooker_processor` inherited a full rectangular snow foot. In rendered pixels this became an obvious flat white plate and violated the no-primitive/no-placeholder visual standard.

## Bounded repair
- Replaced the five station-family snow plates with irregular snow banks plus small dark grounding stones, all kept inside frozen footprints and shallow terrain overlap.
- Strengthened the service workstation with warm timber mass, a blue tool chest, dark apron, oversized hanging axe/tool read, and stronger material blocking.
- Converted the defense platform upper silhouette into a compact watch/guard post with four authored supports, layered blue roof shingles, timber/dark roof structure, localized snow loading, rear windbreak and lamp detail.
- Increased warm/dark timber alternation on service/processing/fishing work surfaces to reduce the washed-out stand-in read.
- No gameplay IDs, sockets, placements, arrangement membership, physics, skeleton, animation, T02/T03 route reserves, or frozen footprints were changed.

## Local validation before durable materialization
Deterministic generator output after this repair:
- catalog: **117,296 triangles**
- camp: **70,984 triangles**
- camp without hearth: **45,016 triangles**
- lakeshore: **43,192 triangles**
- 22 frozen assets
- 11 shared visible material families
- still below the frozen 180,000-triangle catalog ceiling and 48-draw-call arrangement ceiling

Targeted source-integrity generation passed locally. After Godot re-import, `test_task05_station_kit.gd` passed with zero failures, including exact triangle payloads, hashes, bounds, sockets, route clearances, crossing reserves, movement bounds and batching checks.

A second 12-frame Godot quick-look confirmed the crude rectangular station snow plates were gone and the service/defense silhouettes were materially stronger. This is **internal review only**, not an independent critic and not the required exact-source Vulkan acceptance.

## Required next gate
The deterministic materializer must commit exact GLB/catalog bytes from this source. Then the T05 precritic must run from that exact materialized commit and produce the full required actual-Godot evidence set (component, six-angle family, integrated gameplay/use-state, and native 3840×2160 frames). Those pixels must be compared to the newest Havenline references before any >9 score or T05 closure.

T05 remains ACTIVE. T06 remains locked.
