# T09 exact-artifact independent critic review

## Session provenance

- Reviewer task: `/root/t09_final_critic`
- Review timestamp: `2026-09-17T23:43:55Z`
- Review mode: independent, read-only repository audit; scratch contact sheets and this record only
- Candidate commit: `94714f6f65c26a05d78888802c9fb54d31e8c95b`
- Candidate tree: `902e6a876591f9c5c3802f57c64deaa0c44cf1d1`
- Workflow run: `35278615319`
- Artifact ID: `10523722147`
- Artifact directory: `/workspace/scratch/9a5e5c6d5884/t09-final-94714f6-artifact`
- ZIP: `/workspace/scratch/9a5e5c6d5884/t09-final-94714f6.zip`
- ZIP SHA-256, independently recomputed: `751a3998b9556e45861b3b7d62195784e830074de0ca1f0563d9667c1d92dd68`
- Complete-evidence index SHA-256, independently recomputed: `fa557d056078ff4d36e14d1defe3a0549013cd3fc9ef6d7e0a9a48c237f0e532`
- Character 1 GLB SHA-256: `95e4fed3a2778656cdf8b73affd2eb3feda8a32f82f4a0c3f76d90c82633c099`
- Review guidance applied: Havenline T09 frozen R01-R12/G1-G14 contract and character-rigging critic playback/multi-angle/contact rules. Earlier T09 approval and prior failed artifacts were not treated as proof.

## Evidence identity and integrity

- ZIP entries: 1,194.
- Extracted files: 1,194.
- Indexed payload: 1,192 files plus the index and its checksum sidecar.
- Recomputed payload verification: 0 missing, 0 hash mismatches, 0 unindexed payload, 0 indexed-but-absent payload.
- Payload bytes: 146,030,574.
- Inventory: 630 PNG, 414 JPEG, 14 MP4, 97 JSON, 36 logs, 2 text files, 1 SHA-256 sidecar.
- `complete-evidence-index.sha256` matches the independently recomputed index hash.
- Fresh `validate_harvesting.py --candidate 94714f6...` result: PASS, zero errors.
- Tests: 17 suites, 1,006 checks, all pass.
- Save matrix: 7/7 pass.
- Device matrix: 6/6 pass.
- Known failures: empty. Artifact unresolved mandatory defects: empty.

## Visual and motion coverage

- 3/3 complete locked-reference pixels inspected: `A-003.00`, `A-016.00`, `B-028.00`.
- 30/30 isolated authored-tool turntable views inspected.
- 30/30 actor/tool/target contact views inspected.
- 32/32 resource sequence states inspected: wood, stone, metal and fuel across approach, focus, committed contact, recovery, cancellation, re-entry, depletion and respawn.
- 24/24 device screenshots inspected manually.
- 1/1 native 3840x2160 capture inspected.
- 14/14 MP4s decoded without error: six C5 and eight resource-sequence videos.
- 414 resource-sequence source frames covered: wood 102, stone 106, metal 106, fuel 100.
- 510 C5 frames/records covered: 95 real-time cycle, 367 slow-review, 27 turns, 15 close contacts and 6 transitions.
- C5 slow-review duration is approximately 3.85-3.88 times real-time duration, consistent with true 0.25x review playback.
- All 27 turn views and all 15 close-contact views are contact-ready and aligned. Their maximum impact/grip errors are sub-micrometre scale.
- Every real-time and slow cycle includes aligned contact at the authored impact window.
- First and final cycle frames match exactly; all intermediate real/slow frames are unique. The final approach to the seam is smaller than the initial departure in all three clips.

## Device defect recheck: D013 and D015

All four required states were inspected for each profile: phone 16:9, phone 20:9, tablet 16:10, tablet 4:3, foldable outer and foldable inner.

| Profile | Output | Joystick in all 4 | Zero action buttons | Full-frame world | Dark/uniform border rows or columns |
|---|---:|---|---|---|---:|
| phone_16_9 | 1280x720 | PASS | PASS | PASS | 0 |
| phone_20_9 | 1280x576 | PASS | PASS | PASS | 0 |
| tablet_16_10 | 1280x800 | PASS | PASS | PASS | 0 |
| tablet_4_3 | 1024x768 | PASS | PASS | PASS | 0 |
| foldable_outer | 1280x549 | PASS | PASS | PASS | 0 |
| foldable_inner | 1104x884 | PASS | PASS | PASS | 0 |

The bottom-left joystick ROI is non-uniform in all 24 images (`stddev 24.04-31.45`, pixel range `91-103`). Reports agree with pixels: `joystick_active=true`, `permanent_action_buttons=0`, real `InputEventScreenTouch+InputEventScreenDrag`, `joystick_circle_fully_inside_capture_canvas=true`, and `game_canvas_fully_covers_capture_canvas=true`. Projected game-canvas size matches captured pixels in every profile. D013 and D015 are independently VERIFIED CLOSED for this artifact.

## C5 whole-character action ledger

The exact Character 1 GLB contains 66 skin joints. Runtime harvesting clips are installed by the shipping Character 1 motion system, so the standalone GLB release-gate helper is not applicable to these generated engine clips. Coverage instead uses the exact engine-rendered cycles, multi-angle turns, close contacts, transition frames and runtime motion records.

Joint/part mapping used in the audit:

- Root/core: Root, Hip, Pelvis, Waist, Spine01, Spine02.
- Head/neck: NeckTwist01, NeckTwist02, Head; visible hair and eyewear follow the head without detachment.
- Left arm/hand: L_Clavicle, L_Upperarm, L_UpperarmTwist01/02, L_Forearm, L_ForearmTwist01/02, L_Hand.
- Right arm/hand: R_Clavicle, R_Upperarm, R_UpperarmTwist01/02, R_Forearm, R_ForearmTwist01/02, R_Hand.
- Left leg/foot: L_Thigh, L_ThighTwist01/02, L_Calf, L_CalfTwist01/02, L_Foot, L_ToeBase, L_KneePad, four left boot fasteners.
- Right leg/foot: R_Thigh, R_ThighTwist01/02, R_Calf, R_CalfTwist01/02, R_Foot, R_ToeBase, R_KneePad, four right boot fasteners.
- Coat/gear: CoatFront, L_CoatFront, R_CoatFront, PouchSwing and HemFastener_01 through HemFastener_12.

| Part group | chop transforms/deform/clearance/temporal | mine transforms/deform/clearance/temporal | dismantle transforms/deform/clearance/temporal |
|---|---|---|---|
| Root/core | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Head/neck/hair/eyewear | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Left arm/hand/cuff | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Right arm/hand/cuff | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Left leg/foot/knee pad/fasteners | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Right leg/foot/knee pad/fasteners | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Coat/hem/belt/pouches | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |
| Tool grip and target contact | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS | PASS/PASS/PASS/PASS |

Clip-level checks: loop continuity PASS; planted ground contact PASS; action intent PASS; transition into/out of action PASS; preservation PASS; skeleton/animation/export integrity PASS. These are in-place action approvals, not new locomotion or root-motion approval. No unintended knee collapse, ankle convergence, boot crossing, ground penetration, foot skating, garment separation, eyewear/hair detachment, hand/tool separation or tool/body/target clipping was observed.

## Sequence/state findings

- Each wood/stone/metal/fuel report contains exactly two authoritative commits.
- The resource ring, impact, transfer and carried output are visibly resource-specific.
- Maximum simultaneous transfer flight: 1. Maximum impact pulse: 1. Maximum fragments: 2.
- Depletion settles to inactive action, empty tool ID, zero visible fragments, zero visible pulses, zero active flights and zero arrival pulses.
- Respawn is visible and distinct from depletion.
- Cancellation and re-entry preserve inventory authority and do not duplicate a grant.
- Save/reload/migration/rollback matrices preserve inventory, identity, jobs, progression and no-duplicate-grant invariants.

## C6 findings

- Shipping scene, 30-frame warm-up, 180 active-harvest forced-render measurements at 3840x2160 Mobile renderer on llvmpipe.
- Candidate vs exact base: p95 `-189.321 ms`, p99 `-573.948 ms`, average draw calls `+2` within `+12`, primitives `-330.511`, static memory `+1.0578 MB` within `+32`, materials `+2` within `+6`.
- Shader resources +0, physics bodies +0, animation players +0, active animations +0, visible rigs +0, companion population +0.
- Maximum runtime fragments 0 and maximum impact pulses 0 after settling.
- Physical 4K60/display/thermal certification is correctly not claimed and remains outside T09 at T68/T69.

## Independent mandatory scores

Each critic score is the minimum of its mandatory dimensions; no averaging hides a lower dimension.

### C2 Technical / Visual Integrity — 9.34 PASS

- geometry_contact: 9.45
- clipping_seams: 9.34
- intentional_gap_integrity: 9.38
- cross_view_integrity: 9.42

### C3 Havenline Gameplay Identity — 9.31 PASS

- havenline_identity: 9.48
- simple_context_controls: 9.62
- physical_core_loop: 9.46
- complexity_discipline: 9.58
- world_response_readability: 9.31

### C4 Gameplay UX / Readability — 9.22 PASS

- interactable_clarity: 9.34
- danger_clarity: 9.40
- collection_feedback: 9.42
- resource_destination: 9.28
- world_change_clarity: 9.36
- next_action_clarity: 9.22

### C5 Motion / Rigging — 9.18 PASS

- full_cycle: 9.42
- foot_contact: 9.43
- lower_body_mechanics: 9.22
- upper_body_mechanics: 9.34
- weight_transfer: 9.18
- transitions: 9.31
- clipping: 9.38
- secondary_motion_contact: 9.27

### C6 Performance — 9.12 PASS

- frame_time: 9.55
- draw_calls: 9.60
- geometry: 9.64
- texture_memory: 9.35
- shader_cost: 9.70
- physics: 9.65
- animation: 9.62
- population: 9.65
- thermal_risk: 9.12 (T09 software preflight only; physical certification deferred by contract)

**Minimum mandatory critic/dimension: 9.12. Exact artifact critic result: PASS.**

## Defect and closeout disposition

- Exact-artifact unresolved visual, motion, UX, performance or evidence defects: **none**.
- T09-D013: VERIFIED CLOSED by all 24 pixels and corresponding reports.
- T09-D015: VERIFIED CLOSED by all 24 pixels, zero dark/uniform borders, and exact projected-canvas assertions.
- The source defect ledger still labels D015 `FIX_REQUIRED` because it predates this independent final review; this record supplies the independent closure evidence for the exact artifact.
- This artifact review does not establish integration approval. The current integration architecture/toolchain lock reportedly byte-locks the retired T09 workflow at old source `9bc7355...`, records `forward_execution_allowed=false`, and requires full revalidation under explicitly authorized V3.2 scope. No architecture mutation was made in this review.

## Final distinction

- Exact candidate/artifact `94714f6...`: **APPROVE at the independent C2/C3/C4/C5/C6 critic gate**.
- End-to-end integrated T09 closeout in the current integration branch: **BLOCKED pending explicit architecture-scope authorization and governance reconciliation/full revalidation**.

Scratch visual review contact sheets are in `/workspace/scratch/9a5e5c6d5884/t09-final-94714f6-review-assets/`.
