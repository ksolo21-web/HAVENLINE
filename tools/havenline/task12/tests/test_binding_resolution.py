#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/verify_binding_resolution.py"

spec = importlib.util.spec_from_file_location("t12_binding_resolution", TOOL_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class T12BindingResolutionTests(unittest.TestCase):
    def build_repo(self):
        tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "T12 Test"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t12@example.invalid"], cwd=root, check=True)

        t10_data = root / "HavenlineGodot/data/world_transform_recipes.json"
        t11_data = root / "HavenlineGodot/data/camp_construction_recipes.json"
        t10_data.parent.mkdir(parents=True, exist_ok=True)
        t10_data.write_text(json.dumps({"recipes": [{"id": "transform.ready"}]}, indent=2) + "\n")
        t11_data.write_text(json.dumps({"states": [{"id": "camp.ready"}]}, indent=2) + "\n")

        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "accepted upstream data"], cwd=root, check=True)
        accepted_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

        for task in ("T10", "T11"):
            record = root / f"Docs/Production/{task}/verified-completion.json"
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(json.dumps({
                "status": "APPROVED",
                "integrated_source": accepted_sha,
            }, indent=2) + "\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "completion records"], cwd=root, check=True)
        head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

        resolution = {
            "schema_version": 1,
            "task_id": "T12",
            "status": "RESOLVED_FOR_ACTIVATION",
            "allowed_id_kinds_by_task": {
                task: sorted(validator.ALLOWED_ID_KINDS[task])
                for task in validator.EXPECTED_TASKS
            },
            "fact_kind_compatibility": {
                fact_kind: {
                    "source_task": row["source_task"],
                    "accepted_id_kinds": sorted(row["accepted_id_kinds"]),
                }
                for fact_kind, row in validator.FACT_KIND_COMPATIBILITY.items()
            },
            "dependencies": {
                "T10": {
                    "accepted_integrated_source": accepted_sha,
                    "verified_completion_path": "Docs/Production/T10/verified-completion.json",
                    "resolved_public_ids": [{
                        "id": "transform.ready",
                        "kind": "transform_recipe",
                        "source_path": "HavenlineGodot/data/world_transform_recipes.json",
                        "json_pointer": "/recipes/0/id",
                    }],
                },
                "T11": {
                    "accepted_integrated_source": accepted_sha,
                    "verified_completion_path": "Docs/Production/T11/verified-completion.json",
                    "resolved_public_ids": [{
                        "id": "camp.ready",
                        "kind": "camp_state",
                        "source_path": "HavenlineGodot/data/camp_construction_recipes.json",
                        "json_pointer": "/states/0/id",
                    }],
                },
            },
            "promotion_allowed": True,
        }
        return tmp, root, accepted_sha, head_sha, resolution

    def test_resolved_binding_passes_with_accepted_ancestry_and_blobs(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["verified_ids"], 2)

    def test_source_drift_after_approval_fails(self):
        tmp, root, _, _, resolution = self.build_repo()
        with tmp:
            path = root / "HavenlineGodot/data/world_transform_recipes.json"
            data = json.loads(path.read_text())
            data["recipes"].append({"id": "transform.changed-after-approval"})
            path.write_text(json.dumps(data, indent=2) + "\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "unauthorized upstream drift"], cwd=root, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("drifted from accepted integrated source" in e for e in result["errors"]))

    def test_path_escape_fails(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["dependencies"]["T10"]["resolved_public_ids"][0]["source_path"] = "../escape.json"
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("repository-relative safe" in e for e in result["errors"]))

    def test_wrong_upstream_owner_path_fails(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["dependencies"]["T10"]["resolved_public_ids"][0].update({
                "source_path": "HavenlineGodot/data/camp_construction_recipes.json",
                "json_pointer": "/states/0/id",
                "id": "camp.ready",
            })
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("outside T10 accepted ownership" in e for e in result["errors"]))

    def test_cross_task_public_id_ambiguity_fails(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["dependencies"]["T11"]["resolved_public_ids"][0]["id"] = "transform.ready"
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("ambiguous across T10 and T11" in e for e in result["errors"]))

    def test_wrong_t10_id_kind_fails(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["dependencies"]["T10"]["resolved_public_ids"][0]["kind"] = "camp_state"
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("is not allowed for T10" in e for e in result["errors"]))

    def test_fact_kind_compatibility_contract_drift_fails(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["fact_kind_compatibility"]["world_transform_completed"]["accepted_id_kinds"] = ["camp_state"]
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("fact_kind_compatibility drifted" in e for e in result["errors"]))

    def test_completion_record_path_is_frozen(self):
        tmp, root, _, head_sha, resolution = self.build_repo()
        with tmp:
            resolution["dependencies"]["T10"]["verified_completion_path"] = "Docs/Production/T11/verified-completion.json"
            result = validator.validate_resolution(
                resolution,
                require_resolved=True,
                root=root,
                activation_head=head_sha,
            )
        self.assertFalse(result["passed"])
        self.assertTrue(any("verified_completion_path must be Docs/Production/T10" in e for e in result["errors"]))

    def test_preactivation_template_stays_blank_without_git_proof(self):
        template = {
            "schema_version": 1,
            "task_id": "T12",
            "status": "PREPARATION_TEMPLATE_UNRESOLVED",
            "allowed_id_kinds_by_task": {
                task: sorted(validator.ALLOWED_ID_KINDS[task])
                for task in validator.EXPECTED_TASKS
            },
            "fact_kind_compatibility": {
                fact_kind: {
                    "source_task": row["source_task"],
                    "accepted_id_kinds": sorted(row["accepted_id_kinds"]),
                }
                for fact_kind, row in validator.FACT_KIND_COMPATIBILITY.items()
            },
            "dependencies": {
                "T10": {
                    "accepted_integrated_source": "",
                    "verified_completion_path": "Docs/Production/T10/verified-completion.json",
                    "resolved_public_ids": [],
                },
                "T11": {
                    "accepted_integrated_source": "",
                    "verified_completion_path": "Docs/Production/T11/verified-completion.json",
                    "resolved_public_ids": [],
                },
            },
            "promotion_allowed": False,
        }
        result = validator.validate_resolution(template, require_resolved=False)
        self.assertTrue(result["passed"], result["errors"])


if __name__ == "__main__":
    unittest.main()
