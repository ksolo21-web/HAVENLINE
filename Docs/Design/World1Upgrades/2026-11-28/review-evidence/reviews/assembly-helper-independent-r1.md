# Assembly helper r1 — independent review

**Repair required: 8.0/10; 15/16 mandatory checks pass.**

Scope: source and actual dry-run behavior only. No `--apply` or remote publication was executed.

## Finding AS-01

A review without an image hash is marked applicable to current image bytes. A concrete fixture containing only a matching candidate ID, explicit pass verdict and score 10 was promoted to the current status and score. Require an explicit matching image hash for current applicability; retain unbound statements in history and allow an exact-hash root override.

All actual review observations in the tested inventory had matching hashes, so this defect did not misstate a real candidate status in the observed snapshot.

## Verified evidence

The independent dry run completed, retained all six superseded images, both tool-error records, failure history and four nested verifier logs, excluded nested working checkouts, rejected wrong-hash root overrides and positive native flags, and preserved all 50 package files including all 23 frozen design files. It did not create the review-evidence destination.

The snapshot contained 120 curated sources, 21 generated PNGs, 32 crop PNGs and four verifier logs. Counts may grow as art work continues.

Script SHA256: `dc97e0297c2ae223a04a80ab764aa606a7daf2ac239a9dbf4e1e2bf5b313f87e`.

The JSON report contains all gate results, exact evidence hashes and the reproducible failing fixture. No builder files were edited by this critic.
