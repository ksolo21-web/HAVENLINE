# T09 fresh exact-artifact independent final review

## Verdict

**PASS / APPROVED for frozen T09 at exact gameplay source `5415d85838ecf4bea8b3c71662072670e61797a0`.** Every canonical C2/C3/C4/C5/C6 dimension is strictly greater than 9.0 unrounded, the minimum is **9.067**, coverage is complete, and unresolved mandatory defects are **zero**. No previous critic score was reused.

## Provenance and integrity

- Candidate tree: `d9d86772e0231ace00a81ebd69768cf915f8ba2e`
- Workflow run/job: `35289633249` / `105429457120`
- Artifact: `10527144124`
- Verified transfer: `/workspace/scratch/9a5e5c6d5884/t09-5415-verified-transfer.zip`
- ZIP bytes / entries / CRC: `119604425` / `1195` / PASS
- ZIP SHA-256: `78554c4cbdc35710e5261ed217c3eea91a10b4207f20865c7d3b752e06d53e26`
- Complete index SHA-256: `f06ca5ee8a076bce2977069a46e92763b86291f41e8d770b14704a936762f443`
- Indexed payload verification: `1193/1193`, zero missing, zero mismatch, zero extra
- Payload inventory: 630 PNG, 414 JPG, 14 MP4, 97 JSON, 36 log, 2 text; the index and checksum sidecar are additional.
- Provider/model/session: OpenAI / exact runtime model unavailable in session metadata / `/root/t09_final_critic`

The first local download at `t09-final-5415d85.zip` is a rejected truncated transfer: 104,599,552 bytes, SHA-256 `d053d375efb1d3b9f0fb60c752c6c068e93898633debb120e60ec0c6076096be`, `BadZipFile`. It does not redefine the authoritative digest or block G7 because the replacement was independently hashed and CRC-checked.

## Reviewed coverage

- 3/3 locked reference pixels.
- 30/30 isolated authored-tool views and 30/30 in-hand actor/tool/target views.
- 32/32 wood/stone/metal/fuel static states.
- 24/24 device screenshots and 1/1 native 3840x2160 capture.
- 6/6 C5 videos, 8/8 resource-sequence videos, 510 C5 PNG records, 414 sequence frames.
- 71/71 capture reports.
- 17 suites / 1006 checks, 7/7 save cases, 6/6 device profiles.
- `known-failures.json` is indexed at `ec917b06f4485f02508a9c45c617ff7613338883e8b1858dd691d2602dff300d` and has no open failure.

## Fresh mandatory scores

| Critic | Canonical dimensions | Minimum | Status |
|---|---|---:|---|
| C2 | geometry_contact 9.237; clipping_seams 9.184; intentional_gap_integrity 9.163; cross_view_integrity 9.226 | **9.163** | PASS |
| C3 | havenline_identity 9.247; simple_context_controls 9.331; physical_core_loop 9.176; complexity_discipline 9.284; world_response_readability 9.159 | **9.159** | PASS |
| C4 | interactable_clarity 9.171; danger_clarity 9.286; collection_feedback 9.204; resource_destination 9.137; world_change_clarity 9.192; next_action_clarity 9.213 | **9.137** | PASS |
| C5 | full_cycle 9.187; foot_contact 9.229; lower_body_mechanics 9.154; upper_body_mechanics 9.173; weight_transfer 9.108; transitions 9.143; clipping 9.207; secondary_motion_contact 9.132 | **9.108** | PASS |
| C6 | frame_time 9.214; draw_calls 9.402; geometry 9.482; texture_memory 9.237; shader_cost 9.491; physics 9.488; animation 9.472; population 9.489; thermal_risk 9.067 | **9.067** | PASS |

## Concrete findings

- C2: all three tools visibly use authored blue/orange/brown finish. Across isolated, in-hand, turn, close-contact and 4K pixels there is no white silhouette, debug primitive, reversed/floating grip, body penetration or missed contact.
- C3: the four loops preserve the automatic Havenline actor-source-transfer-carry chain and introduce no manual gather/tool/inventory controls. Every device pixel shows one movement joystick and zero action buttons.
- C4: each resource has exactly two authoritative commits, `2→1 / 0→1` then `1→0 / 1→2`. Transfer flight and impact pulse maxima are one. Settled depletion has zero units, hidden source/tool, empty action identity, zero flights/pulses; respawn is visibly distinct.
- C5: real/slow cycle frame counts are chop 29/112, mine 32/124, dismantle 34/131; slow duration is approximately 3.86× real, consistent with true 0.25x review. All 27 turns, 15 close views and each cycle impact window have actual tool, target and aligned contact. Feet/toes/knees/hips, shoulders/elbows/hands, cuffs, boots, belt/pouches, hem, tool grip and target contact are stable, without visible loop pop or clipping.
- C6: exact-base/candidate 3840x2160 software preflight used 30 warm-up plus 180 measured frames. Deltas are p95 `-62.225 ms`, p99 `-500.047 ms`, draw calls `+2`, primitives `-330.511`, static memory `+1.054 MB`, materials `+2`, and shader/physics/animation/population `+0`; all declared limits pass.

## Character-rigging protocol ledger

The runtime evidence exposes 66 joints, all mapped once: root/core 6; head/neck 3; left arm/hand 8; right arm/hand 8; left leg/boot 13; right leg/boot 13; coat/pouch/hem 15. Hair and eyewear were also checked visually with head/neck motion.

| Part group | Chop transform/deform/clearance/temporal | Mine | Dismantle |
|---|---|---|---|
| Root/core | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Head/neck/hair/eyewear | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Left arm/hand/cuff | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Right arm/hand/cuff | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Left leg/foot/knee/fasteners | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Right leg/foot/knee/fasteners | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Coat/hem/belt/pouches | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Tool grip/target contact | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |

Clip-level loop continuity, planted contact, motion intent, entry/exit transition, skeleton integrity, animation integrity and runtime export integrity all pass. This is an approval of the T09 in-place harvesting clips, not new locomotion/root-motion scope.

Primary C5 indexed evidence: `captures/motion-c5/motion.json` (`09455e...643b5`), `motion-hashes.json` (`39a4a1...c5ed1`), and all six videos: chop real/slow (`3086a8...5994`, `a1f080...8e75`), mine (`83bd54...d07c`, `704fd7...e436`), dismantle (`076fc0...bbda`, `99d5a8...fc85`). Full exact hashes and artifact-relative evidence objects are in the machine record.

## D008-D015 closure and gates

All eight repair defects are **VERIFIED_CLOSED**:

- D008 authored finish; D009 actual contact plus 0.25x motion; D010 neutral readable stage/ring; D011 bounded flight/pulse and settled depletion; D012 known-failures indexed; D013 one joystick/zero buttons on all 24 pixels; D014 71 reports and passing typed source/tests; D015 full-frame canvas on all 24 pixels with maximum projected error `0.000122 px` and no dark bands.

Frozen R01-R12 and required G1-G14 each pass. Governance routing commit `460064be8fff1b970071212a923423f2733024cc` passed hosted run `35290773190`; it does not replace the reviewed gameplay source.

## Boundaries

Physical-device 4K60/display and thermal certification are not claimed and remain T68/T69 scope. Approval is limited to the frozen T09 contract and the exact source/artifact identity above.

Machine-readable record: `/workspace/scratch/9a5e5c6d5884/t09-final-5415d85-independent-review.json`.
