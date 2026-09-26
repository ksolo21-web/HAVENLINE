#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "prepare_reconciliation.py"
SPEC = importlib.util.spec_from_file_location("prepare_reconciliation", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReconciliationReservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patterns = [
            "HavenlineGodot/scripts/world_transform.gd",
            "HavenlineGodot/assets/world_transform_v1/**",
            "Docs/Production/T10/**",
            "tools/havenline/task10/**",
            ".github/workflows/havenline-task10-*.yml",
        ]

    def test_task10_workflow_family_is_owned(self) -> None:
        for path in (
            ".github/workflows/havenline-task10-prebuild.yml",
            ".github/workflows/havenline-task10-isolated.yml",
            ".github/workflows/havenline-task10-adapter-preflight.yml",
            ".github/workflows/havenline-task10-preparation.yml",
            ".github/workflows/havenline-task10-world-transformation.yml",
        ):
            self.assertTrue(MODULE.matches_reservation(path, self.patterns), path)

    def test_foreign_task_workflow_is_not_owned(self) -> None:
        self.assertFalse(
            MODULE.matches_reservation(
                ".github/workflows/havenline-task11-camp-construction.yml", self.patterns
            )
        )

    def test_docs_tools_and_asset_subtrees_match(self) -> None:
        for path in (
            "Docs/Production/T10/POST_T09_ADAPTER_CONTRACT.json",
            "tools/havenline/task10/validate_post_t09_adapter.py",
            "HavenlineGodot/assets/world_transform_v1/anchor.glb",
        ):
            self.assertTrue(MODULE.matches_reservation(path, self.patterns), path)

    def test_integration_only_runtime_is_not_reservation_owned(self) -> None:
        self.assertFalse(
            MODULE.matches_reservation("HavenlineGodot/scripts/simulation.gd", self.patterns)
        )


if __name__ == "__main__":
    unittest.main()
