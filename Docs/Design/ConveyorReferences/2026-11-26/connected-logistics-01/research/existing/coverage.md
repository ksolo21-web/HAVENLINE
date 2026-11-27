# Havenline conveyor reference audit

## Coverage and limits

Available visual evidence was inspected for **all 23 registered video identities**: the **2 owner originals**, **8 supplemental full MP4 files**, and **13 YouTube sources available only as archived storyboards**. The review also covered **6 registered stills**, both supplemental reference documents, the locked source manifest and its supplemental manifest. The Nov19 document is preserved at the immutable archive path listed in the index.

| Evidence | Verified coverage |
| --- | --- |
| Original A/B full files | SHA-256 verified; 64 decoded timeline samples, normally 2 seconds apart |
| WS-S01–08 full files | SHA-256 verified; 138 decoded timeline samples, normally 4 seconds apart |
| Primary A late transfer | 11 additional frames at 56.0, 56.5, 57.0, 57.25, 57.5, 57.75, 58.0, 58.25, 58.5, 58.75 and 59.0 seconds |
| YT01–13 | All 122 archived sprite sheets inspected; approximately 10-second previews for YT01 and 1-second previews for the shorts |
| ST01–06 | All 6 actual still images inspected |
| Immutable source documents | 5 files retrieved at commit `e3c787a4ecfffa7ae2013227d2db553f2e2829ef`; each recomputed Git blob hash matches |

**This is not a claim that all videos were played end to end.** Full YouTube streams are unavailable in the current corpus: YT01–07 have recorded HTTP403 failures, while YT08–13 have metadata/posters/storyboards without full video files. Metadata retrieval is not video retrieval. Storyboards cannot verify continuous motion, exact timing or throughput. No audio was reviewed. MP4 timecodes are requested recording seek times; advertisement edits are not gameplay state transitions.

The Nov19 note also names three VidTao creative-thumbnail leads without direct video identities. They remain discovery leads, not three additional watched videos. Three original supplemental analysis-index URLs are retained separately.

## Findings that materially affect the conveyor design

| Source/time | Direct observation | Design implication |
| --- | --- | --- |
| A 14–16s | Shore intake feeds whole fish along an inclined belt into a grill line; cooked whole-fish-shaped stock collects on an output tray. | Distinct intake, processor and output buffer; relative height change is visible. No fillet intermediate is established. |
| A 38–42s | Wheat-like stalks travel on blue belt into a blue processor; round bread-like output stacks appear. | A separate product chain; do not invent an unshown flour stage or exact ingredient ratios. |
| A 56.5–59s | Two adjacent differentiated feed lanes enter a blue burger-marked assembler; short output belt ends at vehicle counter. Finished products move toward car, and cash returns separately to a pad. | Direct machine-to-machine and machine-to-counter conveyors are supported. Exact recipe and numerical rates remain undecided. |
| A 18–56s | Player/helpers carry output stock to pedestrian counters while production continues. | Automation and carry routes coexist. Retain clear worker approaches and stock pickup faces. |
| B 8–12s / 22–28s | Counters sell raw-looking logs and meat matching their order icons. Separate material pads and cash pads sit inside camp; customer queues remain outside. | Counter acceptance must follow its catalogue/order. A blanket ban on raw-material sales would contradict the reference. |
| WS-S04 20–28s | Shore intake ramp discharges fish into a dedicated stock pad; player carries stock to vehicle bays. | Intake-to-buffer is visible; a universal automated warehouse is not proven. |
| WS-S08 24–52s | Perimeter L-shaped roller route links rock-side box and defensive tower; a separate equipment production line ends by a rack and soldier queue. | Optional defensive supply and equipment branches make sense. Exact transported item and ammunition recipe are unverified. |
| YT07 ~31–52s, storyboard only | A perimeter roller path links fish-processing output and pedestrian counter, leaving central floor comparatively open. | Useful spatial precedent for perimeter routing; no full-motion claim. |
| YT09 ~0–47s, storyboard only | Lower resource yard, vertical hoist and upper camp/customer area. | Height-change transport precedent; cycle timing and mechanics remain unverified. |
| WS-S03 44–56s / WS-S05 20–28s | Resource rail/cart routes connect production buildings and furnace. | Fuel logistics precedent; these are rails, not conveyor proof. |

## What remains a Havenline proposal

A universal upgradable storage house, classified receiving docks, reserved dispatch, smart sorters, filtered splitters, mergers, overflow policy, full-buffer backpressure, loop prevention and numerical belt tiers are **design decisions to specify and validate**, not mechanics demonstrated by these reference clips. No source proves that every product must travel through the warehouse before downstream use. A direct production route with controlled reserve/surplus storage is a reasonable design inference.

The supplied footage does not establish exact belt dimensions, throughput, inventory capacities, cooking ratios or ammunition recipes. Do not assign those numbers to a source merely because an item icon or rate-like label appears.

## Evidence and resumption

`source-inventory.json` preserves the full local inventory, hashes, manifests, crop bounds, sample times, coverage gaps and immutable origins. `video-observations.json` contains source-by-source observations and explicit limits. `fullvideo-extraction-manifest.json` and `storyboard-extraction-manifest.json` enumerate the local review sheets. These are reference research outputs, not a game or art approval.

The two attributed public excerpt sheets contain only nine selected frames from owner references A/B: four production/storage/counter examples and five sequential frames from A 58–59s. Full source videos, full storyboard collections and broad timeline sheets remain local. Use `PUBLIC-ARCHIVE-MANIFEST.json` as the positive archive allowlist.

Source A: `Screen_Recording_20260817_124839_YouTube.mp4`, SHA-256 `62f7cfe644de3826cfdd6d91bc23c0ab8d9e4fde3e175c90f762e604547bb0ca`.

Source B: `Screen_Recording_20260817_124510_YouTube.mp4`, SHA-256 `4c9051cbea6df0efa3e7288b13b6d17da46e857274869b0b43d2f96ff6cc79d2`.
