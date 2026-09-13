import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluate_station_reviews import DIMS, SOURCE_GROUPS, evaluate
from final_gate import EXPECTED_DIMENSIONS, MEASUREMENT_NAMES, build_gate


SOURCE = "5" * 40


def row(role, group, passed=True, attempt="primary", seed=1):
    scores = {name: (10.0 if passed else 8.9) for name in DIMS[role]}
    raw = f"{role}:{group}:{attempt}:{seed}".encode()
    board = f"board:{group}".encode()
    board_hash = hashlib.sha256(board).hexdigest()
    candidate_inputs = {f"evidence/{group}.png": "d" * 64}
    pixel_manifest = {
        "candidate_inputs": candidate_inputs,
        "reference_inputs": {"reference/frame.png": "e" * 64},
        "reference_coverage_sha256": "f" * 64,
        "reference_extraction_sha256": "1" * 64,
        "board_sha256": board_hash,
    }
    manifest = json.dumps({
        "candidate_commit": SOURCE, "critic_id": role, "group": group,
        "board_sha256": board_hash, "inputs": candidate_inputs, "pixel_manifest": pixel_manifest,
    }, sort_keys=True).encode()
    return {
        "task": "T05", "source": SOURCE, "critic_id": role, "group": group,
        "candidate_hash": SOURCE, "attempt": attempt, "seed": seed,
        "provider": "local-checksum-pinned-public-model", "model": "Qwen/Qwen3.5-9B",
        "model_revision": "3885219b6810b007914f3a7950a8d1b469d598a5",
        "runtime_release_sha256": "a" * 64, "request_or_run_id": f"run:{role}:{group}:{attempt}:{seed}",
        "input_manifest_path": f"{group}-{seed}-input-manifest.json",
        "input_manifest_hash": hashlib.sha256(manifest).hexdigest(),
        "board_path": f"{group}-{seed}-board.jpg", "board_sha256": board_hash,
        "raw_output_path": f"{group}-{seed}-raw.json", "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
        "reference_scope_complete": True, "independent_execution": True, "error": None,
        "review": {
            "scores": scores, "observations": ["Observed all panels."],
            "defects": [] if passed else ["Visible production defect."],
            "coverage_complete": True, "confidence": "high",
        },
    }


def write_result(root: Path, role: str, attempt: str, rows: list[dict]):
    folder = root / f"{role}-{attempt}"
    folder.mkdir(parents=True)
    for item in rows:
        group = item["group"]
        slice_name = f"{group}-board-01.jpg"
        slice_bytes = f"board:{group}".encode()
        slice_hash = hashlib.sha256(slice_bytes).hexdigest()
        (folder / slice_name).write_bytes(slice_bytes)
        board_payload = {
            "schema_version": 2, "task": "T05", "source": SOURCE, "group": group,
            "layout_contract": {
                "canvas_size": [1600, 1200], "maximum_model_input": [1664, 1664],
                "minimum_reference_display_width": 420, "minimum_candidate_display_height": 480,
                "maximum_candidates_per_board": 2,
            },
            "slices": [{
                "path": slice_name, "sha256": slice_hash, "canvas_size": [1600, 1200],
                "reference_path": "reference/frame.png", "reference_display_size": [420, 980],
                "candidates": [{"path": f"evidence/{group}.png", "display_size": [900, 480]}],
            }],
        }
        board_name = f"{group}-board-manifest.json"
        board = (json.dumps(board_payload, indent=2, sort_keys=True) + "\n").encode()
        (folder / board_name).write_bytes(board)
        board_hash = hashlib.sha256(board).hexdigest()
        candidate_inputs = {f"evidence/{item['group']}.png": "d" * 64}
        manifest_name = f"{group}-input-manifest.json"
        manifest = (json.dumps({
            "candidate_commit": SOURCE, "critic_id": role, "group": item["group"],
            "board_sha256": board_hash, "inputs": candidate_inputs,
            "pixel_manifest": {
                "candidate_inputs": candidate_inputs,
                "reference_inputs": {"reference/frame.png": "e" * 64},
                "reference_coverage_sha256": "f" * 64,
                "reference_extraction_sha256": "1" * 64,
                "board_sha256": board_hash,
                "board_inputs": {slice_name: slice_hash},
            },
        }, sort_keys=True) + "\n").encode()
        (folder / manifest_name).write_bytes(manifest)

        prefix = f"{group}-slice-01"
        raw_name, request_name, answer_name = prefix + "-raw.json", prefix + "-request.json", prefix + "-answer.json"
        raw_slice = json.dumps({
            "id": f"{role}:{group}:{attempt}:{item['seed']}",
            "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(item["review"])}}],
        }).encode()
        request = json.dumps({
            "source_image_path": slice_name, "source_image_sha256": slice_hash,
            "original_size": [1600, 1200], "input_size": [1600, 1200],
            "attempt": attempt, "seed": item["seed"],
        }).encode()
        answer = json.dumps(item["review"]).encode()
        (folder / raw_name).write_bytes(raw_slice)
        (folder / request_name).write_bytes(request)
        (folder / answer_name).write_bytes(answer)
        raw_payload = {
            "schema_version": 2, "task": "T05", "source": SOURCE, "critic_id": role,
            "attempt": attempt, "seed": item["seed"], "group": group,
            "slices": [{
                "board_path": slice_name, "board_sha256": slice_hash,
                "raw_output_path": raw_name, "raw_output_sha256": hashlib.sha256(raw_slice).hexdigest(),
                "request_path": request_name, "request_sha256": hashlib.sha256(request).hexdigest(),
                "answer_path": answer_name, "answer_sha256": hashlib.sha256(answer).hexdigest(),
                "review": item["review"],
            }],
            "aggregate_review": item["review"],
        }
        raw_bundle_name = f"{group}-raw-bundle.json"
        raw = (json.dumps(raw_payload, indent=2, sort_keys=True) + "\n").encode()
        (folder / raw_bundle_name).write_bytes(raw)
        item.update({
            "input_manifest_path": manifest_name, "input_manifest_hash": hashlib.sha256(manifest).hexdigest(),
            "board_path": board_name, "board_sha256": board_hash,
            "raw_output_path": raw_bundle_name, "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
        })
    (folder / "review-result.json").write_text(json.dumps({
        "source": SOURCE, "critic_id": role, "attempt": attempt,
        "candidate_hash": SOURCE, "provider": "local-checksum-pinned-public-model",
        "model": "Qwen/Qwen3.5-9B", "model_revision": "3885219b6810b007914f3a7950a8d1b469d598a5",
        "runtime_release_sha256": "a" * 64,
        "independent_runtime": True, "request_or_run_id": f"run:{role}:{attempt}",
        "competency_passed": True, "error": None, "groups": [item["group"] for item in rows],
        "reviews": rows,
    }))


def write_adjudication(root: Path, role: str, group: str) -> Path:
    primary = root / "primary" / f"{role}-primary"
    result = json.loads((primary / "review-result.json").read_text())
    target = next(item for item in result["reviews"] if item["group"] == group)
    inputs = json.loads((primary / target["input_manifest_path"]).read_text())["pixel_manifest"]
    path = root / "human-adjudication.json"
    path.write_text(json.dumps({
        "candidate_source": SOURCE, "inspection_method": "full_resolution_original_pixels",
        "inspector_kind": "human", "inspector": "independent-reviewer",
        "inspected_at_utc": "2026-09-13T00:00:00Z",
        "decisions": [{"critic_id": role, "group": group, "disposition": "not_corroborated", "inspected_items": inputs}],
    }))
    return path


class VisualQuorumTests(unittest.TestCase):
    def primaries(self, root: Path, dissent=None):
        dissent = dissent or set()
        for role in DIMS:
            write_result(root, role, "primary", [
                row(role, group, (role, group) not in dissent) for group in SOURCE_GROUPS
            ])

    def test_all_primary_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            report = evaluate(root, SOURCE, None)
            self.assertTrue(report["passed"])
            self.assertEqual(report["status"], "PASS")

    def test_single_role_dissent_can_pass_same_role_quorum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary, supplemental = root / "primary", root / "supplemental"
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(primary, {("C1", target)})
            self.assertEqual(evaluate(primary, SOURCE, None)["status"], "ADJUDICATION_REQUIRED")
            for attempt in ("supplement-1", "supplement-2"):
                seed = 2 if attempt == "supplement-1" else 3
                write_result(supplemental, "C1", attempt, [row("C1", target, True, attempt, seed)])
            report = evaluate(primary, SOURCE, supplemental, write_adjudication(root, "C1", target))
            self.assertTrue(report["passed"])
            self.assertEqual(report["status"], "PASS_BY_QUORUM")

    def test_two_primary_failures_cannot_be_outvoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(root, {("C1", target), ("C2", target)})
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["adjudication_requests"], [])

    def test_one_bad_supplement_fails_quorum(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary, supplemental = root / "primary", root / "supplemental"
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(primary, {("C2", target)})
            write_result(supplemental, "C2", "supplement-1", [row("C2", target, False, "supplement-1", 2)])
            write_result(supplemental, "C2", "supplement-2", [row("C2", target, True, "supplement-2", 3)])
            report = evaluate(primary, SOURCE, supplemental, write_adjudication(root, "C2", target))
            self.assertFalse(report["passed"])
            self.assertEqual(report["status"], "FAIL")

    def test_missing_raw_provenance_is_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            target = next(root.rglob("review-result.json"))
            payload = json.loads(target.read_text())
            payload["reviews"][0]["raw_output_sha256"] = "0" * 64
            target.write_text(json.dumps(payload))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertEqual(report["status"], "FAIL")

    def test_duplicate_supplement_seed_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary, supplemental = root / "primary", root / "supplemental"
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(primary, {("C1", target)})
            for attempt in ("supplement-1", "supplement-2"):
                write_result(supplemental, "C1", attempt, [row("C1", target, True, attempt, 2)])
            report = evaluate(primary, SOURCE, supplemental, write_adjudication(root, "C1", target))
            self.assertFalse(report["passed"])
            self.assertIn("freshness", " ".join(report["errors"]))

    def test_supplements_without_human_adjudication_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary, supplemental = root / "primary", root / "supplemental"
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(primary, {("C2", target)})
            write_result(supplemental, "C2", "supplement-1", [row("C2", target, True, "supplement-1", 2)])
            write_result(supplemental, "C2", "supplement-2", [row("C2", target, True, "supplement-2", 3)])
            report = evaluate(primary, SOURCE, supplemental)
            self.assertFalse(report["passed"])
            self.assertIn("human adjudication", " ".join(report["errors"]))

    def test_changed_board_slice_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            slice_path = next(root.rglob("*-board-01.jpg"))
            slice_path.write_bytes(b"changed")
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("board slice", " ".join(report["errors"]))

    def test_passing_aggregate_cannot_hide_low_bound_slice_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            bundle_path = result_path.parent / row_data["raw_output_path"]
            bundle = json.loads(bundle_path.read_text())
            slice_data = bundle["slices"][0]
            dimension = next(iter(slice_data["review"]["scores"]))
            slice_data["review"]["scores"][dimension] = 8.8
            answer_path = result_path.parent / slice_data["answer_path"]
            answer_path.write_text(json.dumps(slice_data["review"]))
            slice_data["answer_sha256"] = hashlib.sha256(answer_path.read_bytes()).hexdigest()
            bundle_path.write_text(json.dumps(bundle))
            row_data["raw_output_sha256"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
            result_path.write_text(json.dumps(result))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("recomputed conservatively", " ".join(report["errors"]))

    def test_duplicate_clean_raw_slice_cannot_omit_another_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            folder = result_path.parent

            board_path = folder / row_data["board_path"]
            board = json.loads(board_path.read_text())
            first = board["slices"][0]
            second = json.loads(json.dumps(first))
            second["path"] = row_data["group"] + "-board-02.jpg"
            second_bytes = b"distinct-second-board"
            (folder / second["path"]).write_bytes(second_bytes)
            second["sha256"] = hashlib.sha256(second_bytes).hexdigest()
            first["candidates"], second["candidates"] = [], first["candidates"]
            board["slices"].append(second)
            board_path.write_text(json.dumps(board))
            board_hash = hashlib.sha256(board_path.read_bytes()).hexdigest()
            row_data["board_sha256"] = board_hash

            manifest_path = folder / row_data["input_manifest_path"]
            manifest = json.loads(manifest_path.read_text())
            manifest["board_sha256"] = board_hash
            manifest["pixel_manifest"]["board_sha256"] = board_hash
            manifest["pixel_manifest"]["board_inputs"][second["path"]] = second["sha256"]
            manifest_path.write_text(json.dumps(manifest))
            row_data["input_manifest_hash"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

            bundle_path = folder / row_data["raw_output_path"]
            bundle = json.loads(bundle_path.read_text())
            bundle["slices"].append(json.loads(json.dumps(bundle["slices"][0])))
            bundle_path.write_text(json.dumps(bundle))
            row_data["raw_output_sha256"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
            result_path.write_text(json.dumps(result))

            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("one-to-one", " ".join(report["errors"]))

    def test_final_gate_binds_visual_to_prior_c6_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            visual_root, performance_root = root / "visual", root / "performance"
            visual_root.mkdir()
            (performance_root / "task05-C6").mkdir(parents=True)
            visual = {
                "source": SOURCE, "passed": True, "status": "PASS_BY_QUORUM",
                "score_averaging": False,
                "decisions": [{"status": "PASS_BY_QUORUM"}], "quorums": [{"group": "core-families"}],
            }
            (visual_root / "final-visual-decision.json").write_text(json.dumps(visual))
            measurement_files = {}
            for relative in MEASUREMENT_NAMES:
                path = performance_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative)
                measurement_files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            input_manifest = {
                "candidate_commit": SOURCE, "baseline_commit": "4" * 40,
                "measurement_files": measurement_files,
            }
            input_path = performance_root / "task05-C6/input-manifest.json"
            input_path.write_text(json.dumps(input_manifest))
            record_path = performance_root / "task05-C6/performance-record.json"
            record_path.write_text('{"mode":"same-runner"}')
            raw_path = performance_root / "candidate-benchmark/benchmark.json"
            c6 = {
                "candidate_commit": SOURCE, "baseline_commit": "4" * 40,
                "passed": True, "defects": [], "mandatory_dimensions": {name: 9.5 for name in EXPECTED_DIMENSIONS},
                "request_or_run_id": "123456:1:source",
                "input_manifest_path": "task05-C6/input-manifest.json", "input_manifest_hash": hashlib.sha256(input_path.read_bytes()).hexdigest(),
                "raw_output_path": "candidate-benchmark/benchmark.json", "raw_output_hash": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "performance_record_path": "task05-C6/performance-record.json", "performance_record_hash": hashlib.sha256(record_path.read_bytes()).hexdigest(),
                "measurement_files": measurement_files,
            }
            (performance_root / "task05-C6/result.json").write_text(json.dumps(c6))
            report = build_gate(visual_root, performance_root, SOURCE, "4" * 40)
            self.assertTrue(report["passed"])
            self.assertEqual(report["C6_run_id"], "123456")


if __name__ == "__main__":
    unittest.main()
