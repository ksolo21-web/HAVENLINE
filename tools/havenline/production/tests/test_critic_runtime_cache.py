from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve()
PRODUCTION = HERE.parents[1]
sys.path.insert(0, str(PRODUCTION))

from prepare_specialist_runtime import prepare_runtime, validate_cached_runtime, validate_runtime_lock


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CriticRuntimeCacheTests(unittest.TestCase):
    def make_fixture(self, root: pathlib.Path):
        payloads = {
            "model.gguf": b"model-bytes",
            "projector.gguf": b"projector-bytes",
            "runtime.tar.gz": b"runtime-archive-bytes",
        }
        lock = {
            "schema_version": 1,
            "publisher": "fixture/publisher",
            "base_model": "fixture/base",
            "revision": "a" * 40,
            "model_file": "model.gguf",
            "projector_file": "projector.gguf",
            "runtime_release": "fixture-runtime",
            "files": [
                {"filename": name, "sha256": sha(data), "url": f"https://invalid.example/{name}"}
                for name, data in payloads.items()
            ],
            "cache_validation": {
                "network_required_on_valid_cache": False,
                "verify_every_file_sha256": True,
                "verify_extracted_llama_server": True,
                "invalid_cache_repairs_from_pinned_urls_only": True,
                "bounded_download_retries": 3,
            },
        }
        root.mkdir(parents=True, exist_ok=True)
        records = []
        for name, data in payloads.items():
            p = root / name
            p.write_bytes(data)
            records.append({"filename": name, "sha256": sha(data), "bytes": len(data)})
        runtime = root / "runtime"
        runtime.mkdir()
        server = runtime / "llama-server"
        server.write_bytes(b"server")
        manifest = {
            "publisher": lock["publisher"],
            "revision": lock["revision"],
            "base_model": lock["base_model"],
            "model_file": lock["model_file"],
            "projector_file": lock["projector_file"],
            "runtime_release": lock["runtime_release"],
            "files": records,
            "purpose": "fixture",
            "paid_inference": False,
            "pinned_revision_enforced": True,
            "offline_cache_validation": True,
        }
        (root / "manifest.json").write_text(json.dumps(manifest))
        return lock

    def test_runtime_lock_schema_is_strict(self):
        with tempfile.TemporaryDirectory() as td:
            lock = self.make_fixture(pathlib.Path(td))
            result = validate_runtime_lock(lock)
            self.assertTrue(result["passed"], result["errors"])
            self.assertEqual(result["file_count"], 3)

    def test_valid_cache_is_fully_hash_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            lock = self.make_fixture(root)
            result = validate_cached_runtime(root, lock)
            self.assertTrue(result["passed"], result["errors"])
            self.assertEqual(len(result["files"]), 3)

    def test_valid_cache_requires_zero_network_access(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            lock = self.make_fixture(root)
            with mock.patch("prepare_specialist_runtime.urllib.request.urlopen", side_effect=AssertionError("network must not be used")), mock.patch("prepare_specialist_runtime.download", side_effect=AssertionError("download must not be used")):
                result = prepare_runtime(root, lock)
            self.assertTrue(result["passed"])
            self.assertEqual(result["source"], "verified_cache")
            self.assertFalse(result["network_used"])

    def test_corrupt_cache_is_rejected_before_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            lock = self.make_fixture(root)
            (root / "model.gguf").write_bytes(b"tampered")
            result = validate_cached_runtime(root, lock)
            self.assertFalse(result["passed"])
            self.assertTrue(any("cached SHA-256 mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
