# Havenline production evidence

Each task owns a subdirectory `TXX/`. Frozen candidate evidence must be
exact-source-bound and packaged by `tools/havenline/production/evidence_packager.py`.

Preserve tests/logs, deterministic captures, motion evidence where applicable,
performance records, save/device matrices, raw critic inputs/outputs, failures
and dispositions. Do not overwrite failed evidence; create a new candidate/run
subdirectory.
