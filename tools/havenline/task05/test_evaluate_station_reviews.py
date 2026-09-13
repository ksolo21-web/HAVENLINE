import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from evaluate_station_reviews import DIMS, SOURCE_GROUPS, evaluate
from final_gate import EXPECTED_DIMENSIONS, MEASUREMENT_NAMES, build_gate
from review_protocol import (
    FILES, GROUP_FAMILIES, PROTOCOL, REFERENCE_FOCUS_BOXES,
    applicable_dimensions, build_review_prompt, build_review_schema,
    build_slice_contract, build_slice_plan, expected_request_settings,
    persist_model_response, review_exit_code, review_integrity_errors,
    write_incomplete_group_bundle,
)


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
        "reference_scope_complete": True, "independent_execution": True, "execution_complete": True, "error": None,
        "review": {
            "scores": scores, "observations": ["Observed all panels."],
            "defects": [] if passed else ["Visible production defect."],
            "defect_evidence": [],
            "coverage_complete": True, "confidence": "high",
        },
    }


def write_result(root: Path, role: str, attempt: str, rows: list[dict]):
    folder = root / f"{role}-{attempt}"
    folder.mkdir(parents=True)
    for item in rows:
        group = item["group"]
        reference_bindings = {family: [f"reference/{family}.png"] for family in GROUP_FAMILIES[group]}
        candidate_inputs = {candidate: "d" * 64 for candidate in FILES[group]}
        plan = build_slice_plan(group, reference_bindings)
        slices = []
        raw_slices = []
        board_inputs = {}
        slice_scopes = {}
        intended_pass = item["review"]["defects"] == []
        for index, scope in enumerate(plan, 1):
            family = scope["reference_family"]
            slice_name = f"{group}-board-{index:02d}.jpg"
            slice_bytes = f"board:{group}:{family}".encode()
            slice_hash = hashlib.sha256(slice_bytes).hexdigest()
            (folder / slice_name).write_bytes(slice_bytes)
            candidate_paths = scope["candidate_paths"]
            reference_path = scope["reference_path"]
            focus_name = f"reference-focus-{family}.png"
            source_name = f"reference-source-{family}.png"
            source_path = folder / source_name
            focus_path = folder / focus_name
            if not source_path.exists():
                Image.new("L", (1080, 1950), 80).save(source_path)
            if not focus_path.exists():
                with Image.open(source_path) as source_image:
                    source_image.crop(tuple(REFERENCE_FOCUS_BOXES[family])).save(focus_path)
            source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            focus_hash = hashlib.sha256(focus_path.read_bytes()).hexdigest()
            board_inputs[slice_name] = slice_hash
            slice_scopes[slice_name] = {
                "reference_family": family, "reference_path": reference_path,
                "candidate_paths": candidate_paths, "comparison_mode": scope["comparison_mode"],
                "unseen_assets_out_of_scope": True,
                "reference_source_path": source_name,
                "reference_source_sha256": source_hash,
                "reference_focus_path": focus_name,
                "reference_focus_sha256": focus_hash,
                "reference_focus_crop_box": REFERENCE_FOCUS_BOXES[family],
            }
            slices.append({
                "path": slice_name, "sha256": slice_hash, "canvas_size": [1600, 1200],
                "reference_path": reference_path, "reference_family": family,
                "comparison_mode": scope["comparison_mode"], "unseen_assets_out_of_scope": True,
                "reviewed_candidate_paths": candidate_paths,
                "reference_display_size": [500, 650],
                "reference_source_path": source_name,
                "reference_source_sha256": source_hash,
                "reference_focus_path": focus_name,
                "reference_focus_sha256": focus_hash,
                "reference_focus_crop_box": REFERENCE_FOCUS_BOXES[family],
                "candidates": [{"path": candidate_path, "display_size": [900, 480]} for candidate_path in candidate_paths],
            })

            prefix = f"{group}-slice-{index:02d}"
            raw_name, request_name, answer_name = prefix + "-raw.json", prefix + "-request.json", prefix + "-answer.json"
            dimensions = applicable_dimensions(role, candidate_paths)
            is_dissent_slice = not intended_pass and index == 1
            defect_evidence = [
                {
                    "candidate_path": candidate_paths[0], "dimension": dimension,
                    "visible_region": "center fixture", "description": f"Visible {dimension} production defect.",
                }
                for dimension in dimensions
            ] if is_dissent_slice else []
            slice_review = {
                "scores": {dimension: (8.9 if is_dissent_slice else 10.0) for dimension in dimensions},
                "observations": ["Observed all panels."],
                "defects": [evidence["description"] for evidence in defect_evidence],
                "defect_evidence": defect_evidence,
                "coverage_complete": True, "confidence": "high",
                "reviewed_candidate_paths": candidate_paths,
                "reference_path_used": reference_path,
                "unseen_assets_out_of_scope_acknowledged": True,
            }
            raw_slice = json.dumps({
                "id": f"{role}:{group}:{attempt}:{item['seed']}:{index}",
                "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(slice_review)}}],
            }).encode()
            request_contract = build_slice_contract(SOURCE, role, attempt, group, index, len(plan), slices[-1])
            request_settings = expected_request_settings(role, attempt, item["seed"])
            request = json.dumps({
                "model": request_settings["model"],
                "prompt": build_review_prompt(SOURCE, role, request_contract),
                "schema": build_review_schema(role, candidate_paths, reference_path),
                "request_contract": request_contract, "request_settings": request_settings,
                "source_image_path": slice_name, "source_image_sha256": slice_hash,
                "original_size": [1600, 1200], "input_size": [1600, 1200],
                "seed": item["seed"],
            }).encode()
            answer = json.dumps(slice_review).encode()
            (folder / raw_name).write_bytes(raw_slice)
            (folder / request_name).write_bytes(request)
            (folder / answer_name).write_bytes(answer)
            raw_slices.append({
                "board_path": slice_name, "board_sha256": slice_hash,
                "reviewed_candidate_paths": candidate_paths, "reference_family": family, "reference_path": reference_path,
                "raw_output_path": raw_name, "raw_output_sha256": hashlib.sha256(raw_slice).hexdigest(),
                "request_path": request_name, "request_sha256": hashlib.sha256(request).hexdigest(),
                "answer_path": answer_name, "answer_sha256": hashlib.sha256(answer).hexdigest(),
                "review": slice_review,
            })

        defect_evidence = []
        seen_evidence = set()
        for slice_data in raw_slices:
            for evidence in slice_data["review"]["defect_evidence"]:
                key = json.dumps(evidence, sort_keys=True)
                if key not in seen_evidence:
                    seen_evidence.add(key)
                    defect_evidence.append(evidence)
        item["review"] = {
            "scores": {
                dimension: min(
                    slice_data["review"]["scores"][dimension]
                    for slice_data in raw_slices if dimension in slice_data["review"]["scores"]
                )
                for dimension in DIMS[role]
            },
            "observations": ["Observed all panels."],
            "defects": [evidence["description"] for evidence in defect_evidence],
            "defect_evidence": defect_evidence,
            "coverage_complete": True, "confidence": "high",
        }

        board_payload = {
            "schema_version": 4, "protocol": PROTOCOL,
            "task": "T05", "source": SOURCE, "group": group,
            "required_reference_families": list(GROUP_FAMILIES[group]),
            "reference_bindings": reference_bindings,
            "layout_contract": {
                "canvas_size": [1600, 1200], "maximum_model_input": [1664, 1664],
                "minimum_reference_display_width": 500, "minimum_candidate_display_height": 480,
                "maximum_candidates_per_board": 2, "coverage_complete_is_slice_local": True,
                "unlisted_assets_may_not_be_scored_as_missing": True,
            },
            "slices": slices,
        }
        board_name = f"{group}-board-manifest.json"
        board = (json.dumps(board_payload, indent=2, sort_keys=True) + "\n").encode()
        (folder / board_name).write_bytes(board)
        board_hash = hashlib.sha256(board).hexdigest()
        manifest_name = f"{group}-input-manifest.json"
        manifest = (json.dumps({
            "candidate_commit": SOURCE, "critic_id": role, "group": item["group"],
            "board_sha256": board_hash, "inputs": candidate_inputs,
            "pixel_manifest": {
                "candidate_inputs": candidate_inputs,
                "reference_inputs": {
                    f"reference/{family}.png": hashlib.sha256((folder / f"reference-source-{family}.png").read_bytes()).hexdigest()
                    for family in GROUP_FAMILIES[group]
                },
                "reference_bindings": reference_bindings,
                "slice_scopes": slice_scopes,
                "reference_coverage_sha256": "f" * 64,
                "reference_extraction_sha256": "1" * 64,
                "board_sha256": board_hash,
                "board_inputs": board_inputs,
            },
        }, sort_keys=True) + "\n").encode()
        (folder / manifest_name).write_bytes(manifest)
        raw_payload = {
            "schema_version": 4, "task": "T05", "source": SOURCE, "critic_id": role,
            "attempt": attempt, "seed": item["seed"], "group": group,
            "execution_complete": True, "slices": raw_slices,
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
        "competency_passed": True, "execution_complete": True, "error": None, "groups": [item["group"] for item in rows],
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


def mutate_bound_request(result_path: Path, mutate) -> None:
    result = json.loads(result_path.read_text())
    row_data = result["reviews"][0]
    bundle_path = result_path.parent / row_data["raw_output_path"]
    bundle = json.loads(bundle_path.read_text())
    slice_data = bundle["slices"][0]
    request_path = result_path.parent / slice_data["request_path"]
    request = json.loads(request_path.read_text())
    mutate(request)
    request_path.write_text(json.dumps(request))
    slice_data["request_sha256"] = hashlib.sha256(request_path.read_bytes()).hexdigest()
    bundle_path.write_text(json.dumps(bundle))
    row_data["raw_output_sha256"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    result_path.write_text(json.dumps(result))


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

    def test_protocol_planner_covers_all_77_candidates_once_with_matched_references(self):
        seen = []
        for group in FILES:
            references = {family: [f"reference/{family}.png"] for family in GROUP_FAMILIES[group]}
            plan = build_slice_plan(group, references)
            candidates = [path for item in plan for path in item["candidate_paths"]]
            self.assertEqual(set(candidates), set(FILES[group]))
            self.assertEqual(len(candidates), len(set(candidates)))
            self.assertEqual({item["reference_family"] for item in plan}, set(GROUP_FAMILIES[group]))
            self.assertTrue(all(item["reference_path"] in references[item["reference_family"]] for item in plan))
            self.assertTrue(all(item["unseen_assets_out_of_scope"] is True for item in plan))
            seen.extend(candidates)
        self.assertEqual(len(seen), 77)
        self.assertEqual(len(seen), len(set(seen)))

    def test_single_candidate_slice_omits_cross_view_dimension(self):
        candidates = ["component/camp-night-front.png"]
        self.assertEqual(
            applicable_dimensions("C1", candidates),
            ["reference_fidelity", "visual_language"],
        )
        schema = build_review_schema("C1", candidates, "reference/B-008.00.png")
        self.assertNotIn("cross_view_consistency", schema["properties"]["scores"]["properties"])

    def test_low_score_without_localized_defect_evidence_is_invalid(self):
        candidates = ["component/camp-night-front.png"]
        review = {
            "scores": {"reference_fidelity": 8.9, "visual_language": 9.7},
            "defects": [], "defect_evidence": [],
        }
        errors = review_integrity_errors(review, "C1", candidates)
        self.assertIn("lacks localized defect evidence", " ".join(errors))

    def test_defect_evidence_must_bind_declared_candidate_and_dimension(self):
        candidates = ["component/camp-night-front.png"]
        description = "Visible base penetration at the lower-left contact plate."
        review = {
            "scores": {"reference_fidelity": 8.9, "visual_language": 9.7},
            "defects": [description],
            "defect_evidence": [{
                "candidate_path": "component/not-on-this-slice.png",
                "dimension": "reference_fidelity", "visible_region": "lower left",
                "description": description,
            }],
        }
        errors = review_integrity_errors(review, "C1", candidates)
        self.assertIn("outside the bound slice scope", " ".join(errors))

    def test_changed_reference_focus_crop_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            focus_path = next(root.rglob("reference-focus-*.png"))
            focus_path.write_bytes(b"changed-focus")
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("reference focus crop", " ".join(report["errors"]))

    def test_wrong_family_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            board_path = result_path.parent / row_data["board_path"]
            board = json.loads(board_path.read_text())
            first = board["slices"][0]
            first["reference_family"] = board["required_reference_families"][1]
            board_path.write_text(json.dumps(board))
            row_data["board_sha256"] = hashlib.sha256(board_path.read_bytes()).hexdigest()
            manifest_path = result_path.parent / row_data["input_manifest_path"]
            manifest = json.loads(manifest_path.read_text())
            manifest["board_sha256"] = row_data["board_sha256"]
            manifest["pixel_manifest"]["board_sha256"] = row_data["board_sha256"]
            manifest_path.write_text(json.dumps(manifest))
            row_data["input_manifest_hash"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            result_path.write_text(json.dumps(result))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("wrong-family reference", " ".join(report["errors"]))

    def test_missing_unseen_asset_scope_guard_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            board_path = result_path.parent / row_data["board_path"]
            board = json.loads(board_path.read_text())
            board["slices"][0]["unseen_assets_out_of_scope"] = False
            board_path.write_text(json.dumps(board))
            row_data["board_sha256"] = hashlib.sha256(board_path.read_bytes()).hexdigest()
            manifest_path = result_path.parent / row_data["input_manifest_path"]
            manifest = json.loads(manifest_path.read_text())
            manifest["board_sha256"] = row_data["board_sha256"]
            manifest["pixel_manifest"]["board_sha256"] = row_data["board_sha256"]
            manifest_path.write_text(json.dumps(manifest))
            row_data["input_manifest_hash"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            result_path.write_text(json.dumps(result))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("unseen-asset scope guard", " ".join(report["errors"]))

    def test_model_candidate_path_acknowledgment_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            bundle_path = result_path.parent / row_data["raw_output_path"]
            bundle = json.loads(bundle_path.read_text())
            slice_data = bundle["slices"][0]
            changed_review = json.loads(json.dumps(slice_data["review"]))
            changed_review["reviewed_candidate_paths"] = ["evidence/not-on-this-slice.png"]
            answer_path = result_path.parent / slice_data["answer_path"]
            answer_path.write_text(json.dumps(changed_review))
            slice_data["answer_sha256"] = hashlib.sha256(answer_path.read_bytes()).hexdigest()
            raw_path = result_path.parent / slice_data["raw_output_path"]
            raw = json.loads(raw_path.read_text())
            raw["choices"][0]["message"]["content"] = json.dumps(changed_review)
            raw_path.write_text(json.dumps(raw))
            slice_data["raw_output_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            slice_data["review"] = changed_review
            bundle_path.write_text(json.dumps(bundle))
            row_data["raw_output_sha256"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
            result_path.write_text(json.dumps(result))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("model did not acknowledge exact candidate paths", " ".join(report["errors"]))

    def test_altered_global_inventory_prompt_is_rejected_even_when_rehashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            mutate_bound_request(result_path, lambda request: request.update({"prompt": "Judge the full inventory on every slice."}))
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("exact protocol prompt", " ".join(report["errors"]))

    def test_altered_dynamic_schema_is_rejected_even_when_rehashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            mutate_bound_request(
                result_path,
                lambda request: request["schema"]["properties"]["reviewed_candidate_paths"].update({"maxItems": 99}),
            )
            report = evaluate(root, SOURCE, None)
            self.assertFalse(report["passed"])
            self.assertIn("exact dynamic response schema", " ".join(report["errors"]))

    def test_supplement_claimed_seed_must_match_bound_request_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary, supplemental = root / "primary", root / "supplemental"
            target = sorted(SOURCE_GROUPS)[0]
            self.primaries(primary, {("C1", target)})
            write_result(supplemental, "C1", "supplement-1", [row("C1", target, True, "supplement-1", 2)])
            write_result(supplemental, "C1", "supplement-2", [row("C1", target, True, "supplement-2", 3)])
            result_path = supplemental / "C1-supplement-1/review-result.json"
            mutate_bound_request(result_path, lambda request: request["request_settings"].update({"seed": 999}))
            report = evaluate(primary, SOURCE, supplemental, write_adjudication(root, "C1", target))
            self.assertFalse(report["passed"])
            self.assertIn("claimed role, attempt, and seed", " ".join(report["errors"]))

    def test_incomplete_row_reports_exact_truncation_without_path_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.primaries(root)
            result_path = next(root.rglob("review-result.json"))
            result = json.loads(result_path.read_text())
            row_data = result["reviews"][0]
            row_data.update({"execution_complete": False, "independent_execution": False, "error": "truncated core-families-slice-03"})
            for key in ("board_sha256", "raw_output_sha256", "raw_output_path"):
                row_data.pop(key, None)
            result["execution_complete"] = False
            result_path.write_text(json.dumps(result))
            report = evaluate(root, SOURCE, None)
            joined = " ".join(report["errors"])
            self.assertIn("truncated core-families-slice-03", joined)
            self.assertNotIn("invalid board_sha256", joined)
            self.assertNotIn("invalid raw_output_path", joined)

    def test_producer_truncation_preserves_raw_and_request_then_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = root / "slice-request.json"
            raw_path = root / "slice-raw.json"
            answer_path = root / "slice-answer.json"
            request_path.write_text('{"request_contract":"bound-before-call"}')
            raw_bytes = json.dumps({
                "choices": [{"finish_reason": "length", "message": {"content": "{\"partial\":"}}],
            }).encode()
            with self.assertRaisesRegex(RuntimeError, "truncated group-slice-01"):
                persist_model_response(raw_bytes, raw_path, answer_path, "group-slice-01")
            failed_slice = {
                "request_path": request_path.name,
                "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
                "raw_output_path": raw_path.name,
                "raw_output_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "error": "truncated group-slice-01",
            }
            bundle_path = root / "group-raw-bundle.json"
            bundle = write_incomplete_group_bundle(
                bundle_path, source=SOURCE, role="C1", attempt="primary", seed=1,
                group="core-families", slices=[], failed_slice=failed_slice,
            )
            self.assertEqual(raw_path.read_bytes(), raw_bytes)
            self.assertTrue(request_path.is_file())
            self.assertFalse(answer_path.exists())
            self.assertFalse(bundle["execution_complete"])
            self.assertEqual(review_exit_code(bundle["execution_complete"]), 1)

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
            raw_path = performance_root / "candidate-a/benchmark.json"
            c6 = {
                "candidate_commit": SOURCE, "baseline_commit": "4" * 40,
                "passed": True, "defects": [], "mandatory_dimensions": {name: 9.5 for name in EXPECTED_DIMENSIONS},
                "request_or_run_id": "123456:1:source",
                "input_manifest_path": "task05-C6/input-manifest.json", "input_manifest_hash": hashlib.sha256(input_path.read_bytes()).hexdigest(),
                "raw_output_path": "candidate-a/benchmark.json", "raw_output_hash": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "performance_record_path": "task05-C6/performance-record.json", "performance_record_hash": hashlib.sha256(record_path.read_bytes()).hexdigest(),
                "measurement_files": measurement_files,
            }
            (performance_root / "task05-C6/result.json").write_text(json.dumps(c6))
            report = build_gate(visual_root, performance_root, SOURCE, "4" * 40)
            self.assertTrue(report["passed"])
            self.assertEqual(report["C6_run_id"], "123456")


if __name__ == "__main__":
    unittest.main()
