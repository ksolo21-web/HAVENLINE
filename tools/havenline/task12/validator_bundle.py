#!/usr/bin/env python3
"""Deterministic digest for the acceptance-critical T12 validator bundle."""
from __future__ import annotations

import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]

VALIDATOR_BUNDLE_FILES = (
    "tools/havenline/task12/validate_progression_contract.py",
    "tools/havenline/task12/verify_binding_resolution.py",
    "tools/havenline/task12/validate_candidate_evidence.py",
    "tools/havenline/task12/validate_critic_review_records.py",
    "tools/havenline/task12/validate_evidence_index.py",
    "tools/havenline/task12/validate_data_schema.py",
    "tools/havenline/task12/compare_engine_parity.py",
    "tools/havenline/task12/final_candidate_gate.py",
    "tools/havenline/production/workstream.py",
    "Docs/Production/T12/PROGRESSION_DATA_SCHEMA.json",
    "Docs/Production/T12/RUNTIME_INTERFACE_CONTRACT.json",
    "Docs/Production/T12/ENGINE_TEST_VECTORS.json",
    "Docs/Production/T12/ENGINE_PARITY_OUTPUT_SCHEMA.json",
)


def bundle_digest(root: pathlib.Path = ROOT) -> str:
    digest = hashlib.sha256()
    for relative in sorted(VALIDATOR_BUNDLE_FILES):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"validator bundle file missing: {relative}")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def main() -> None:
    print(bundle_digest())


if __name__ == "__main__":
    main()
