# Counter stock point near-side study: HOLD

Counter-local geometry only. Exact recorded stock position (surface 2), exact 528-triangle original edge-connected board, original inboard idle pivot reconstruction and all 13,624 independently matched donor triangles from frozen native witness. Candidate (0, 1.077068, +.105) m on imported surface 2 triangle 3879 is one near-side centerline diagnostic, not a new marker. Both hand-to-point segments remain blocked well before the endpoint, though nearer distance drops from roughly 1.513 m to 1.421 m. Sampling at x=0 (+z 5 mm pitch, original stock height ±40 mm, withholding outermost 15 mm from eligibility) is not a searched aisle, height envelope, usable prop space, dynamic/curved hand path, body or eye clearance, or integrated service. No exterior customer/payment/marker or other scope change; no approved arm motion, render, runtime or new authorization.

Reproduce against exact frozen originals with NumPy/SciPy:
```sh
OPENBLAS_NUM_THREADS=1 python study.py PINNED_INDEPENDENT_CHECK_PY EXACT_COUNTER_CUSTODY_ROOT EXACT_PRIOR_COUNTER_RUN > rebuilt.json
cmp rebuilt.json result.json
```
