# Actual task-packet verification — R2

**103/103 checks passed; 0 failed.**
Actual generator calls: 9/9 succeeded; both deliberate invalid-data calls were rejected, with zero packet writes.

This report verifies prospective packet content and rejection behavior. It grants no game, motion, visual, device or activation approval.

## Actual packet captures

| Task | CG IDs | Selected CD IDs | Output SHA-256 |
|---|---|---|---|
| T01 | CG15, CG16 | none | cf15cc7d8e4202ffcab51d765d8ff3b6dc8ffef605775958ce056a5f7197fd14 |
| T23 | CG02, CG03, CG04, CG05, CG06, CG07, CG09, CG10, CG11, CG12, CG13, CG14, CG15, CG16, CG18, CG19, CG20, CG21, CG22 | CD01, CD02, CD03, CD04, CD05, CD06, CD07, CD08, CD09, CD10, CD12 | 94ae0cf4a83075cb64543b9e916ea1b9837ae2665636531de18f36543a6e4dd8 |
| T26 | CG01, CG03, CG04, CG05, CG07, CG13, CG14, CG15, CG16 | CD01, CD02, CD04, CD05, CD06, CD07 | cb9bf57c9ec986163926ecb107e85a1ba5c0229775f3eaee1b8b35ab5837b86e |
| T27 | CG01, CG03, CG04, CG05, CG07, CG13, CG14, CG15, CG16 | CD01, CD02, CD04, CD05, CD06, CD07 | dba6338d5d8593d900aad86e3fe17db8488f59306b96b39d11fc14ab9e9c5f82 |
| T33 | CG02, CG03, CG05, CG08, CG09, CG10, CG11, CG15, CG16, CG19, CG20, CG21, CG22 | CD01, CD02, CD03, CD04, CD05, CD08, CD09, CD11, CD12 | 6fe4dad486845c983da8847654c67c022eb0ea2fd940fc62fc842469fc2cec9f |
| T43 | CG03, CG05, CG06, CG12, CG15, CG16, CG20, CG21, CG22, CG23 | CD01, CD02, CD03, CD04, CD05, CD08, CD09, CD12 | 1231d0f44be7968ad1bd5e387cc260496fe3c425bfb3f7afce03cadddbcc5f59 |
| T44 | CG04, CG07, CG08, CG09, CG10, CG15, CG16, CG19 | CD01, CD02, CD06, CD07, CD08, CD11, CD12 | 0f2ea58921003b5bed28258fd1e58f86178ee33e4b0afbba57b61bc593838931 |
| T58 | CG05, CG11, CG15, CG16, CG17, CG18, CG23 | CD04, CD05, CD10 | 4e4d5b5212d7ec9cad4b05189b510a79a28a5dab0787ee69e6172b222471160e |
| T70 | CG01, CG15, CG16, CG17, CG20, CG21, CG22, CG23, CG24 | CD04, CD05, CD08, CD09, CD10, CD12 | 1c483f8bfe184f36c4993b3281bc0a8c899e8fed4006c7bd5bdb862d1ffe8bf3 |

## Rejection probes

- **removed_fox_attack:** {'type': 'SystemExit', 'message': 'Invalid resource/actor declarations: required pet fox missing named attack profile fox_attack; attack-capable actor fox has no explicit attack animation profile; T26 required_profiles_by_task references unknown profile fox_attack; T31 required_profiles_by_task references unknown profile fox_attack; T26 required_attack_profiles_by_task references unknown profile fox_attack'}; packet writes: 0.
- **missing_level_099_outcome:** {'type': 'ValueError', 'message': 'Invalid completeness contract: 100 distinct authored outcomes required'}; packet writes: 0.

## Preservation and source binding

15 existing canonical packets remained byte-identical. All nine requested Evidence output paths retained their prior existence/absence. 163 guarded source/input files remained unchanged.
Generator, completeness validator, resource validator, verification script, every captured output and all canonical before/after hashes are bound in the JSON report.

R1 preserves all21 original files byte-for-byte. R2 distinguishes audited baseline3fad812, observed cutoff2f46e72 and reported Build13 gameplay source2654f50. The actual updated completeness check verified all152 source bindings; Build13 game-test values remain reported, not reexecuted here.

T44 retains regional contact/use-state C5 evidence even for approved-clip reuse; animation_delta=false does not waive contact proof and reuse does not require a new clip.

Every packet retains applicable GD obligations, the current CG/CD decisions, explicit supersession of D01–D05 behavior choices, required reading of the current Codex source selector, >=9.9 unrounded reference checks and stronger exact-10 visual gates.

## Limits

- Captured packets are prospective output; historical canonical packets remain unchanged.
- Current source selection is dereferenced from the required selector file: audited baseline3fad812, observed cutoff2f46e72 and reported Build13 source2654f50 remain separate. No live branch fetch or gameplay editing performed.
- The updated completeness source validator was run for152 source bindings; reported Build13 gameplay tests and media playback were not reexecuted.
- Dates in captured packet bodies are the real generator timestamps and are included in raw output hashes.
- Path.mkdir and Path.write_text were intercepted for every main call; a separate audit hook blocked direct candidate mutations.
- The older GD decision wording remains historical; the following CD section explicitly supersedes those open behavior choices.
- Static declaration and fail-fast checks do not prove pet attacks, 100 levels, animation, economy balance, runtime safety or reference-match scores.
