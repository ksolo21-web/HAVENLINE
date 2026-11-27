# Independent execution evidence

These are the separate critic's raw reports, deterministic fixtures, scripts and output, copied byte-for-byte after the product freeze. [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json) binds the copied files. [Final review](../../FINAL_REVIEW.md) names the actual reviewed scope and remaining game gates.

- `native-suite-stdout.txt`: independent rerun of the builder's 107-check native suite on an exact source copy.
- `retest-recovery-cases.json`: 16 independently authored coupled recovery checks, all passing.
- `exact-count-oracle-result.json`: 120 deterministic cases and 360 arithmetic comparisons against Python arbitrary-precision expected values, all passing.
- `reviewed-source-sha256.json`: the exact source identities used by the critic.
- `repro-frozen-payer.json` and its script: preserved reproduction of the earlier funding-owner deadlock. This is rejected-history evidence, not a failing result on the final candidate.

From a repository root with Godot 4.7.2 installed, the current independent scripts can be rerun against the reviewed component:

```sh
vehicle_review_repo="$PWD"
godot --headless --path "$vehicle_review_repo/tools/havenline/vehicle_rules" --script "$vehicle_review_repo/Docs/Production/SnowTruckGarage/2026-11-27/evidence/independent-review/retest_recovery_cases.gd"
godot --headless --path "$vehicle_review_repo/tools/havenline/vehicle_rules" --script "$vehicle_review_repo/Docs/Production/SnowTruckGarage/2026-11-27/evidence/independent-review/review_count_oracle.gd"
```

The scripts write their result beside their own script. Preserve the original receipt before intentionally generating a different candidate's results. Exact arithmetic and fixture-world transitions do not prove real contact, reachable resources, scene geometry, whole-world persistence, animation, audio or mobile performance.
