#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
TOOL_PATH = ROOT / "tools/havenline/task12/validator_bundle.py"

spec = importlib.util.spec_from_file_location("t12_validator_bundle", TOOL_PATH)
bundle = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bundle)


class T12ValidatorBundleTests(unittest.TestCase):
    def make_fixture(self):
        tmp = tempfile.TemporaryDirectory()
        root = pathlib.Path(tmp.name)
        for relative in bundle.VALIDATOR_BUNDLE_FILES:
            src = ROOT / relative
            dst = root / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
        return tmp, root

    def test_repository_bundle_digest_is_deterministic(self):
        first = bundle.bundle_digest(ROOT)
        second = bundle.bundle_digest(ROOT)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^sha256:[0-9a-f]{64}$")

    def test_any_bundle_file_change_changes_digest(self):
        tmp, root = self.make_fixture()
        with tmp:
            before = bundle.bundle_digest(root)
            target = root / bundle.VALIDATOR_BUNDLE_FILES[0]
            target.write_bytes(target.read_bytes() + b"\n# mutation canary\n")
            after = bundle.bundle_digest(root)
        self.assertNotEqual(before, after)

    def test_missing_bundle_file_fails_closed(self):
        tmp, root = self.make_fixture()
        with tmp:
            (root / bundle.VALIDATOR_BUNDLE_FILES[-1]).unlink()
            with self.assertRaises(FileNotFoundError):
                bundle.bundle_digest(root)


if __name__ == "__main__":
    unittest.main()
