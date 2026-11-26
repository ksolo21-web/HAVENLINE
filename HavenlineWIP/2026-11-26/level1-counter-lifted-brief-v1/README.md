# Lifted handoff input brief: HOLD, no curve authored

Exact 66-joint Character 1 source, original fit-to-1.75m runtime rule, pinned native inboard idle and same-board near-lip witness. The same stock board has 528 edge-welded triangles and reaches at most +0.124984 m counter-local Z. The nominated on-board point is (0, 1.077068, +0.105) m. Pivot dimensions refer to wrist origins, not fingertips, mitten surfaces or an intended grasp.

At stock fit (1.786304923×), exact shoulder-to-elbow and elbow-to-wrist chain lengths are 0.164010 m and 0.198642 m each side, ≈0.362651 m combined. With fixed shoulder origin and nominal link lengths, *any* rotation-only wrist path can span no more than the sphere diameter, 0.725303 m, from the measured original wrist position. The same-board endpoint is ≈1.4208 m from both wrists, ≈0.6954 m beyond this deliberately generous bound. An over-top curve cannot solve the endpoint condition **for a wrist at that point and that fixed-shoulder model**. Rotation-only fixed clavicle-origin generous full-chain diameter is 1.37117 m left (insufficient), 1.44915 m right (a weak non-exclusion, not reachable motion). At the fixed measured Head anchor a looser all-neck/clavicle/spine-branch triangle sum similarly excludes left by 30.55 mm and leaves right only a 9.40 mm theoretical margin before constraints. None of this is a maximum human reach, impossibility of skin/prop contact with unknown offset, a tested shoulder world pose, free root/lean, an animation, or authority for a change.

Dependencies before a real probe: exact approved service contact or grasp patch and its offset in the wrist frame, immutable first service animation candidate or explicitly authorized motion bounds for shoulder/clavicle/body/root, measured corresponding posed transform and permitted clearance over the real lip, and independent trajectory/no-visual-regression review. Current GLB only has idle/walk/run; no authored service track or contact authority. Without those inputs there is no plausible supported lifted route to draw. No engine, source edits, asset/service handoff, payment, release or asset copies.

```sh
OPENBLAS_NUM_THREADS=1 python measure.py PINNED_COUNTER_CHECKER EXACT_COUNTER_CUSTODY EXACT_PRIOR_COUNTER_RUN EXACT_LEVEL1_PROJECT PINNED_NEAR_STOCK_RESULT > rebuilt.json
cmp rebuilt.json result.json
```
