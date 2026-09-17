from __future__ import annotations

import copy
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from factory_closeout_gate import validate

SHA = "a" * 40
ENV = "b" * 64


def good_observation():
    return {
        "schema_version": 1,
        "passed": True,
        "task_id": "T10",
        "source_sha": SHA,
        "environment_exact": True,
        "environment_fingerprint": ENV,
        "bundle_is_observation_not_authority": True,
        "quality_thresholds_unchanged": True,
        "telemetry": {
            "source_sha": SHA,
            "task_id": "T10",
            "queue_seconds": 2.0,
            "run_seconds": 30.0,
            "gate_durations": {"sentinel": 5.0},
            "rerun_count": 0,
            "c0_cycles": 0,
            "proof_cache_hits": 1,
            "artifact_bytes": 100,
            "terminal_gate": "closeout",
            "terminal_class": "SUCCESS",
        },
        "task_state": {
            "task_id": "T10",
            "candidate_commit": SHA,
            "snapshot_is_derived_not_authority": True,
        },
        "runtime_dependency_traces": [],
    }


class FactoryCloseoutGateTests(unittest.TestCase):
    def test_exact_success_observation_passes_without_granting_approval(self):
        r = validate("T10", SHA, good_observation())
        self.assertTrue(r["passed"], r["errors"])
        self.assertFalse(r["approval_authority_granted"])
        self.assertTrue(r["factory_observation_required"])

    def test_failure_or_stale_source_cannot_close(self):
        cases=[]
        failed=good_observation();failed["telemetry"]["terminal_class"]="FAILURE";cases.append(failed)
        stale=good_observation();stale["source_sha"]="c"*40;cases.append(stale)
        no_env=good_observation();no_env["environment_exact"]=False;no_env["environment_fingerprint"]=None;cases.append(no_env)
        authority=good_observation();authority["bundle_is_observation_not_authority"]=False;cases.append(authority)
        for row in cases:
            self.assertFalse(validate("T10",SHA,row)["passed"])

    def test_t09_is_not_retroactively_reopened_by_forward_gate(self):
        r = validate("T09", SHA, good_observation())
        self.assertFalse(r["passed"])
        self.assertTrue(any("forward-only" in e for e in r["errors"]))

    def test_unvalidated_runtime_dependency_trace_blocks_closeout(self):
        row=good_observation();row["runtime_dependency_traces"]=[{"trace":{"source_sha":SHA},"validation":{"passed":False}}]
        r=validate("T10",SHA,row)
        self.assertFalse(r["passed"])
        self.assertTrue(any("not validated" in e for e in r["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
