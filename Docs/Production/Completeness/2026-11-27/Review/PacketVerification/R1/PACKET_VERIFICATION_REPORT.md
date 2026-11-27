# Actual task-packet verification

**97/97 checks passed; 0 failed.**
Actual generator calls: 9/9 succeeded; both deliberate invalid-data calls were rejected, with zero packet writes.

This report verifies prospective packet content and rejection behavior. It grants no game, motion, visual, device or activation approval.

## Actual packet captures

| Task | CG IDs | Selected CD IDs | Output SHA-256 |
|---|---|---|---|
| T01 | CG15, CG16 | none | a0e9980e12787829bcb0da740fddc049da0e262910c4864c50c6a628969f9f65 |
| T23 | CG02, CG03, CG04, CG05, CG06, CG07, CG09, CG10, CG11, CG12, CG13, CG14, CG15, CG16, CG18, CG19, CG20, CG21, CG22 | CD01, CD02, CD03, CD04, CD05, CD06, CD07, CD08, CD09, CD10, CD12 | 5d4f73da7db56816a79a2e8e25fe008897989277ee1365e253a79ba82ff84b6e |
| T26 | CG01, CG03, CG04, CG05, CG07, CG13, CG14, CG15, CG16 | CD01, CD02, CD04, CD05, CD06, CD07 | 80ffd19e9fca528d2eb3fd326cc9e253ca2a9bbaa3fb9ecbd9e4cf03b1dc6a5a |
| T27 | CG01, CG03, CG04, CG05, CG07, CG13, CG14, CG15, CG16 | CD01, CD02, CD04, CD05, CD06, CD07 | ec72fe280b9be585d8036724081006dbf436c00764a08c46a255f3fd39471ba5 |
| T33 | CG02, CG03, CG05, CG08, CG09, CG10, CG11, CG15, CG16, CG19, CG20, CG21, CG22 | CD01, CD02, CD03, CD04, CD05, CD08, CD09, CD11, CD12 | 6b72a7b65d39adb06dcb0c38ae0ec5c986ce3f360cb9a70cfe4d6a98134de309 |
| T43 | CG03, CG05, CG06, CG12, CG15, CG16, CG20, CG21, CG22, CG23 | CD01, CD02, CD03, CD04, CD05, CD08, CD09, CD12 | eef6e7bbd73d0070b3dbad05ae933ad6a560c681506373d8ce17602a9e44968a |
| T44 | CG04, CG07, CG08, CG09, CG10, CG15, CG16, CG19 | CD01, CD02, CD06, CD07, CD08, CD11, CD12 | 605e6ff8e3cf7b5805bc5cc4bd32726143ad3eb9394f5ad39c6a4aad06708f25 |
| T58 | CG05, CG11, CG15, CG16, CG17, CG18, CG23 | CD04, CD05, CD10 | 9e44b79c6fb6eecb75138ce5410532cd7dac70d510a88cb0840a82c134fbb67a |
| T70 | CG01, CG15, CG16, CG17, CG20, CG21, CG22, CG23, CG24 | CD04, CD05, CD08, CD09, CD10, CD12 | 19dfda26e8da278ea38b27b2ea8a91776810adea284c9cdfbfb32522f04a7f31 |

## Rejection probes

- **removed_fox_attack:** {'type': 'SystemExit', 'message': 'Invalid resource/actor declarations: required pet fox missing named attack profile fox_attack; attack-capable actor fox has no explicit attack animation profile; T26 required_profiles_by_task references unknown profile fox_attack; T31 required_profiles_by_task references unknown profile fox_attack; T26 required_attack_profiles_by_task references unknown profile fox_attack'}; packet writes: 0.
- **missing_level_099_outcome:** {'type': 'ValueError', 'message': 'Invalid completeness contract: 100 distinct authored outcomes required'}; packet writes: 0.

## Preservation and source binding

15 existing canonical packets remained byte-identical. All nine requested Evidence output paths retained their prior existence/absence. 161 guarded source/input files remained unchanged.
Generator, completeness validator, resource validator, verification script, every captured output and all canonical before/after hashes are bound in the JSON report.

T44 retains regional contact/use-state C5 evidence even for approved-clip reuse; animation_delta=false does not waive contact proof and reuse does not require a new clip.

Every packet retains applicable GD obligations, the current CG/CD decisions, explicit supersession of D01–D05 behavior choices, required reading of the current Codex source selector, >=9.9 unrounded reference checks and stronger exact-10 visual gates.

## Limits

- Captured packets are prospective output; historical canonical packets remain unchanged.
- Current source selection is dereferenced from the required selector file; no live branch fetch or gameplay source editing performed.
- Dates in captured packet bodies are the real generator timestamps and are included in raw output hashes.
- Path.mkdir and Path.write_text were intercepted for every main call; a separate audit hook blocked direct candidate mutations.
- The older GD decision wording remains historical; the following CD section explicitly supersedes those open behavior choices.
- Static declaration and fail-fast checks do not prove pet attacks, 100 levels, animation, economy balance, runtime safety or reference-match scores.
