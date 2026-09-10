# Havenline — east-to-west lake correction complete

**Accepted correction: PASS at the minimum 9/10 task gate. Both independent critic roles have a lowest required score of 9.5/10.** This is a scoped lake/terrain approval, not a full-game release or physical-device performance certificate.

## What changed

The lake now extends across the entire playable east-west width. Its length increased from **10.4 to 30.4 world units (2.923 times as long)**. Water runs from x=-15.2 to x=15.2, beyond the playable limits x=-14.2 and x=14.2. The lake is centred at x=0, while the north-south centre, width and water elevation remain unchanged.

The basin, rounded snowbanks, water material and movement boundary share the same lake definition. Saved actors formerly in the water or isolated north strip recover to connected dry shoreline without losing carried or stored inventory. The historical progression contract and prices remain unchanged; its now-submerged north approach is resolved to the dry shore in the runtime copy. The shoreline still permits east-west walking and rejects sprinting through water. Dressing placement no longer leaves shrub/rock tops projecting through the enlarged water.

The longer surface exposed broad color bands. The final repair enables **material debanding** and restores the original lit water shader. Sun/moon lighting, ambient response, fog, received shadows and saved-time ripples remain. The unsuccessful custom ambient-emission workaround was removed. The final water is one opaque mesh with 2,568 triangles; this is not a stretched screenshot, unlit plane, blur or resolution reduction.

## Exact accepted source and evidence

- Game source: `25cf9ea5a31ef0acc90fbc4612498dc671565ccb`.
- Build, captures and both critic roles: Actions run `34543229258`.
- Render evidence artifact: `10178191106`, ZIP SHA-256 `f81c6d0eba95009b8b61409628321917c0446ee4610d4585a8728b930cd7de8a`.
- Exact source artifact: `10178192391`, ZIP SHA-256 `ef5a057f4c05d22622a10d5762101deb8a2f720cc6837daba9c96d00461542bd`.
- Combined raw reviews/gate artifact: `10178268819`, ZIP SHA-256 `db9029999be6d84e18b1f748819443442f6cc5ffbf82fb189fb95da7141ba162`.

All downloaded ZIP digests were checked against GitHub's returned digests. All actual image, changed-runtime and protected-file hashes were independently checked again in the local closure verification.

## Completed checks

| Check | Verified result |
|---|---|
| Engine regression assertions | **750/750** across 14 suites, both locally and on GitHub |
| Existing tree geometry checks | **9/9** |
| Final exact-source/evidence checks | **375/375** |
| Reference-fidelity review | **9/9 groups passed; minimum 9.5/10** |
| Visual-integrity review | **9/9 groups passed; minimum 9.5/10** |
| Actual source-bound images | **59**, including **22 at 3840 × 2160, scale 1.0** |
| Original and approved GLBs | **All 33 unchanged** |
| Approved perimeter forest | **586 instances remain above water** |
| Wet/rim/north-strip recovery | **15,390 positions checked** |
| Legacy-save scenarios | **28**, with inventory preserved |
| Matched lighting return | Initial and returned daytime images are byte-identical |

The two roles executed independently through the publisher's public Qwen3-VL-235B-A22B demo, application revision `eb7f245e2c0d3b573dd8ed6addca9b7f6af26847`. They use the same declared model, not two diverse model families or human reviewers. Hosted model weights were not downloaded or locally attested. Blind image-recognition controls, original requests, exact input boards and raw model responses are retained. No completed low-score response was retried just to improve its number; bounded retries apply only to incomplete transport/response failures, which are also retained.

## Actual-output inspection and limits

The full-width, top-down, west-bank, east-bank, rear-shore and normal gameplay images were inspected, together with all 59 frames in their grouped sequences and relevant native closeups. The new span is continuous. The broad triangular color bands are absent. Day, dusk, night, dawn, blizzard-night and return-to-day use the same diagnostic camera; unrelated character poses are held only during those six controlled captures. Normal runtime animations are unchanged.

Some raw reviewer wording extrapolates beyond a cropped frame. Those statements were not treated as proof. In particular, a cropped tree-visibility view cannot establish full-lake extent, and the fidelity extent response contains numeric scores but no explanatory observations. The dedicated geometry tests, actual full-width/top-down images and the integrity role's explicit extent description establish that requirement. Raw scores and wording are preserved, not rewritten. Finite polygonal shoreline approximation is visible in close diagnostic views of the existing ground mesh; this accepted 9.5/10 correction is not represented as perfect final-game surfacing.

Earlier failed runs, incorrect hypotheses, initial banded renders and the previous short-lake approval remain historical evidence. The previous approval was reopened rather than applied to changed geometry. The material-debanding comparison that established the final fix is run `34542759625`; viewport-only debanding did not remove the bands.

## Scope and next-task protection

No later gameplay task was implemented. No character GLB or approved tree model was changed. Characters 2–4's final rigging/review remains last. No unfinished APK was delivered, and no testing or benchmarking is assigned to Kaleb.

The lake correction restores T02's intermediate task pass. Subsequent work remains unstarted. Complete-game functionality, final reference-video fidelity, automatic physical phone/tablet behavior and sustained native 4K/60 remain separate mandatory release gates. Actual native-resolution frames are resolution evidence only; they are not proof of sustained 60 FPS or thermals on Android hardware.
