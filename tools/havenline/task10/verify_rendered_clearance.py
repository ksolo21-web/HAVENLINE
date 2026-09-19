#!/usr/bin/env python3
"""Verify the T10 representative label/response probe from retained rasters."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

CONTRACT = "T10_RENDERED_CLEARANCE_REPRESENTATIVE_PROBE_V1"
STATES = ("ready", "blocked", "preview", "committing", "complete", "replay")
KNOWN_FAILED_STATES = ("preview", "committing", "complete", "replay")
LAYER_NAMES = ("normal", "response_only", "background", "label_id_background", "label_id")
EXPECTED_CAPTURE_SIZE = (3840, 2160)
MIN_CLEARANCE_PX = 12.0
CLEARANCE_HEIGHT_RATIO = 0.015
SAFE_INSET_RATIO = 0.025
PIXEL_THRESHOLD = 1
ISOLATION = {
    "normal": {"label_visible": True, "response_visible": True, "floor_visible": True,
               "caption_visible": True, "id_background": False, "label_id_white": False},
    "response_only": {"label_visible": False, "response_visible": True, "floor_visible": True,
                      "caption_visible": True, "id_background": False, "label_id_white": False},
    "background": {"label_visible": False, "response_visible": False, "floor_visible": True,
                   "caption_visible": True, "id_background": False, "label_id_white": False},
    "label_id_background": {"label_visible": False, "response_visible": False, "floor_visible": False,
                            "caption_visible": False, "id_background": True, "label_id_white": True},
    "label_id": {"label_visible": True, "response_visible": False, "floor_visible": False,
                 "caption_visible": False, "id_background": True, "label_id_white": True},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def difference_mask(left: Image.Image, right: Image.Image) -> Image.Image:
    if left.size != right.size:
        raise ValueError("layer sizes differ")
    diff = ImageChops.difference(left.convert("RGB"), right.convert("RGB"))
    red, green, blue = diff.split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return maximum.point(lambda value: 255 if value >= PIXEL_THRESHOLD else 0, mode="L")


def count_mask(mask: Image.Image) -> int:
    return mask.histogram()[255]


def mask_bbox(mask: Image.Image) -> list[int]:
    box = mask.getbbox()
    return list(box) if box else []


def image_is_black(image: Image.Image) -> bool:
    return image.convert("RGB").getbbox() is None


def safe_layer_path(root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or relative.suffix.lower() != ".png":
        raise ValueError("rendered layer path must be a relative PNG")
    unresolved = root / relative
    if unresolved.is_symlink():
        raise ValueError("rendered layer may not be a symlink")
    root = root.resolve()
    path = unresolved.resolve()
    if path == root or root not in path.parents:
        raise ValueError("rendered layer path escapes artifact root")
    return path


def expected_layer_name(state: str, layer: str) -> str:
    suffix = {
        "normal": "",
        "response_only": "-response-only",
        "background": "-background",
        "label_id_background": "-label-id-background",
        "label_id": "-label-id",
    }[layer]
    return f"{state}-gameplay{suffix}.png"


def grayscale_identity_pass(image: Image.Image) -> bool:
    red, green, blue = image.convert("RGB").split()
    return (ImageChops.difference(red, green).getextrema()[1] <= 3
            and ImageChops.difference(red, blue).getextrema()[1] <= 3)


def bbox_clearance(left: list[int], right: list[int]) -> int:
    horizontal = max(right[0] - left[2], left[0] - right[2], 0)
    vertical = max(right[1] - left[3], left[1] - right[3], 0)
    return max(horizontal, vertical)


def dilate_square(mask: Image.Image, radius: int) -> Image.Image:
    """Binary square dilation via a bounded integral image, avoiding huge rank kernels."""
    source = np.asarray(mask, dtype=np.uint8) != 0
    padded = np.pad(source, ((radius, radius), (radius, radius)), constant_values=False)
    integral = np.pad(padded.astype(np.uint8), ((1, 0), (1, 0))).cumsum(
        axis=0, dtype=np.int32
    ).cumsum(axis=1, dtype=np.int32)
    kernel = radius * 2 + 1
    window = (integral[kernel:, kernel:] - integral[:-kernel, kernel:]
              - integral[kernel:, :-kernel] + integral[:-kernel, :-kernel])
    return Image.fromarray(np.where(window > 0, 255, 0).astype(np.uint8), mode="L")


def finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def finite_vector(value, length: int) -> bool:
    return isinstance(value, list) and len(value) == length and all(finite_number(item) for item in value)


def valid_transform(value) -> bool:
    return (isinstance(value, dict)
            and set(value) == {"basis_x", "basis_y", "basis_z", "origin"}
            and all(finite_vector(value[key], 3) for key in value))


def expected_geometry(logical_size: list[int]) -> tuple[float, list[float]]:
    width, height = map(float, logical_size)
    clearance = max(MIN_CLEARANCE_PX, height * CLEARANCE_HEIGHT_RATIO)
    inset = max(MIN_CLEARANCE_PX, min(width, height) * SAFE_INSET_RATIO)
    return clearance, [inset, inset, width - inset * 2.0, height - inset * 2.0]


def close_list(actual, expected, tolerance=1e-5) -> bool:
    return (isinstance(actual, list) and len(actual) == len(expected)
            and all(finite_number(a) and math.isclose(float(a), float(e), rel_tol=0.0, abs_tol=tolerance)
                    for a, e in zip(actual, expected)))


def validate_core(core: dict, *, state: str, angle: str, nonce: str,
                  logical_size: list[int], renderer: str, expected_identity: dict,
                  resource_symbols_sha256: str) -> None:
    if core.get("case_nonce") != nonce or core.get("state") != state or core.get("angle") != angle:
        raise ValueError(f"{state}: wrong case binding")
    if core.get("viewport") != logical_size:
        raise ValueError(f"{state}: viewport binding mismatch")
    for key, value in expected_identity.items():
        if core.get(key) != value:
            raise ValueError(f"{state}: {key} binding mismatch")
    if core.get("renderer") != renderer or not renderer.startswith("mobile/"):
        raise ValueError(f"{state}: unexpected renderer binding")
    if not valid_transform(core.get("camera_transform")):
        raise ValueError(f"{state}: missing camera transform")
    for key in ("visual_root_transform", "label_transform", "ring_transform", "ghost_transform"):
        if not valid_transform(core.get(key)):
            raise ValueError(f"{state}: missing {key}")
    if (not finite_number(core.get("camera_fov")) or not math.isclose(float(core["camera_fov"]), 48.0)
            or core.get("camera_projection") != 0 or not finite_number(core.get("camera_size"))
            or not finite_number(core.get("camera_near")) or float(core["camera_near"]) <= 0.0
            or not finite_number(core.get("camera_far")) or float(core["camera_far"]) <= float(core["camera_near"])
            or not isinstance(core.get("camera_keep_aspect"), int)):
        raise ValueError(f"{state}: incomplete camera projection binding")
    descriptor = core.get("lifecycle_descriptor")
    expected_lifecycle = "complete" if state == "replay" else state
    if (not isinstance(descriptor, dict) or descriptor.get("lifecycle") != expected_lifecycle
            or not isinstance(core.get("label_text"), str) or not core["label_text"]
            or descriptor.get("feedback_text") != core.get("label_text")):
        raise ValueError(f"{state}: incomplete lifecycle/text binding")
    expected_phase = 0.25 / 1.4 if state == "committing" else 0.0
    if (not finite_number(core.get("dynamic_phase_seconds"))
            or not math.isclose(float(core["dynamic_phase_seconds"]), expected_phase,
                                rel_tol=0.0, abs_tol=1e-6)):
        raise ValueError(f"{state}: wrong frozen dynamic phase")
    realization = core.get("label_realization")
    if (not isinstance(realization, dict) or not finite_vector(realization.get("offset"), 2)
            or not finite_number(realization.get("width")) or float(realization["width"]) <= 0.0
            or realization.get("fixed_size") is not False
            or not finite_number(realization.get("pixel_size"))
            or not math.isclose(float(realization["pixel_size"]), 0.0057, rel_tol=0.0, abs_tol=1e-9)
            or realization.get("billboard") != 1 or realization.get("no_depth_test") is not True
            or realization.get("render_priority") != 100
            or realization.get("outline_render_priority") != 99):
        raise ValueError(f"{state}: incomplete Label3D realization binding")
    font = core.get("font_identity")
    version = font.get("engine_version", {}) if isinstance(font, dict) else {}
    if (not isinstance(font, dict) or not font.get("class") or font.get("fallback_count") != 1
            or font.get("font_size") != 38 or font.get("outline_size") != 9
            or font.get("resource_symbols_path") != "res://assets/world_transform_v1/resource_symbols.tres"
            or font.get("resource_symbols_sha256") != resource_symbols_sha256
            or not isinstance(version, dict) or [version.get(k) for k in ("major", "minor", "patch")] != [4, 7, 2]):
        raise ValueError(f"{state}: missing font/resource identity")


def report_errors(report: dict, *, expect_variant: str | None = None) -> list[str]:
    errors: list[str] = []
    rows = report.get("rows", [])
    if report.get("contract") != CONTRACT or report.get("domain_complete") is not False:
        errors.append("wrong representative-probe contract")
    if expect_variant and report.get("variant") != expect_variant:
        errors.append("wrong variant")
    if len(rows) != 6 or {row.get("state") for row in rows} != set(STATES):
        errors.append("six unique lifecycle rows required")
    for row in rows:
        state = row.get("state")
        if not row.get("label_mask_pixels"):
            errors.append(f"{state}: empty label mask")
        if not row.get("response_mask_pixels"):
            errors.append(f"{state}: empty response mask")
        if not row.get("source_files_bound", False):
            errors.append(f"{state}: source layers not bound")
        if report.get("variant") == "candidate" and not row.get("safe_frame_passed", False):
            errors.append(f"{state}: rendered label leaves safe frame")
    if report.get("variant") == "candidate" and report.get("failure_count") != 0:
        errors.append("candidate has rendered-clearance failures")
    if report.get("variant") == "baseline":
        missing = sorted(set(KNOWN_FAILED_STATES) - set(report.get("direct_failure_states", [])))
        if missing:
            errors.append(f"baseline missed known direct failures: {missing}")
    return errors


def verify(root: Path, manifest_path: Path, masks_root: Path, source: str,
           product_blob_sha256: str, variant: str, probe_source: str,
           capture_sha256: str, verifier_sha256: str, workflow_sha256: str,
           resource_symbols_sha256: str,
           expected_capture_size: tuple[int, int] = EXPECTED_CAPTURE_SIZE) -> dict:
    manifest = json.loads(manifest_path.read_text())
    identity = manifest.get("rendered_clearance_identity", {})
    expected_identity = {
        "product_source": source,
        "product_view_sha256": product_blob_sha256,
        "probe_source": probe_source,
        "probe_capture_sha256": capture_sha256,
        "probe_verifier_sha256": verifier_sha256,
        "probe_workflow_sha256": workflow_sha256,
    }
    if manifest.get("candidate") != source or identity != expected_identity:
        raise ValueError("manifest rendered-clearance identity mismatch")
    if sha256(Path(__file__)) != verifier_sha256:
        raise ValueError("running verifier does not match bound verifier hash")
    if manifest.get("rendered_clearance_probe") is not True or manifest.get("angles") != ["gameplay"]:
        raise ValueError("manifest is not a representative gameplay probe")
    logical_size = manifest.get("logical_size")
    if (not isinstance(logical_size, list) or len(logical_size) != 2
            or not all(isinstance(value, int) and value > 0 for value in logical_size)):
        raise ValueError("invalid logical viewport")
    capture_size = manifest.get("capture_resolution")
    if capture_size != list(expected_capture_size):
        raise ValueError("physical capture resolution is not the independently expected size")
    if manifest.get("native_scale_1") is not (tuple(expected_capture_size) == EXPECTED_CAPTURE_SIZE):
        raise ValueError("native-scale claim does not match expected capture")
    renderer = manifest.get("renderer")
    if not isinstance(renderer, str) or not renderer.startswith("mobile/"):
        raise ValueError("unexpected manifest renderer")
    records = manifest.get("records", [])
    if len(records) != 6 or {record.get("state") for record in records} != set(STATES):
        raise ValueError("representative probe requires six unique state records")

    masks_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    seen_nonces: set[str] = set()
    seen_paths: set[Path] = set()
    required_logical, expected_frame = expected_geometry(logical_size)
    for record in records:
        state = record.get("state")
        angle = record.get("angle")
        if state not in STATES or angle != "gameplay":
            raise ValueError("unexpected state/angle record")
        layers = record.get("rendered_clearance_layers", {})
        layer_records = layers.get("layer_records", {})
        if set(layer_records) != set(LAYER_NAMES) or layers.get("process_frozen") is not True:
            raise ValueError(f"{state}: incomplete frozen layer records")
        nonce = layers.get("case_nonce")
        expected_nonce = hashlib.sha256(f"{source}:{probe_source}:{state}:gameplay".encode()).hexdigest()
        if nonce != expected_nonce or nonce in seen_nonces:
            raise ValueError(f"{state}: invalid or reused case nonce")
        seen_nonces.add(nonce)

        paths: dict[str, Path] = {}
        cores: list[dict] = []
        independent_core_hashes: set[str] = set()
        for layer_name in LAYER_NAMES:
            layer = layer_records[layer_name]
            if layer.get("isolation") != ISOLATION[layer_name]:
                raise ValueError(f"{state}/{layer_name}: isolation contract mismatch")
            if layer.get("file") != expected_layer_name(state, layer_name):
                raise ValueError(f"{state}/{layer_name}: unexpected case/pass filename")
            path = safe_layer_path(root, str(layer.get("file", "")))
            if path in seen_paths:
                raise ValueError(f"{state}/{layer_name}: rendered layer path reused")
            seen_paths.add(path)
            if not path.is_file() or path.is_symlink() or sha256(path) != layer.get("sha256"):
                raise ValueError(f"{state}/{layer_name}: missing or substituted rendered layer")
            core = layer.get("core")
            core_json = layer.get("core_json")
            if (not isinstance(core, dict) or not isinstance(core_json, str)
                    or json.loads(core_json) != core
                    or hashlib.sha256(core_json.encode()).hexdigest() != layer.get("core_sha256")):
                raise ValueError(f"{state}/{layer_name}: invalid serialized core binding")
            validate_core(core, state=state, angle=angle, nonce=nonce,
                          logical_size=logical_size, renderer=renderer,
                          expected_identity=expected_identity,
                          resource_symbols_sha256=resource_symbols_sha256)
            cores.append(core)
            independent_core_hashes.add(hashlib.sha256(core_json.encode()).hexdigest())
            paths[layer_name] = path
        if any(core != cores[0] for core in cores[1:]) or len(independent_core_hashes) != 1:
            raise ValueError(f"{state}: camera/state/dynamic binding changed between passes")
        if paths["normal"].name != record.get("file"):
            raise ValueError(f"{state}: normal layer does not match record")

        images = {name: Image.open(path).convert("RGBA") for name, path in paths.items()}
        sizes = {image.size for image in images.values()}
        if sizes != {tuple(expected_capture_size)} or record.get("size") != list(expected_capture_size):
            raise ValueError(f"{state}: physical capture size binding mismatch")
        if any(image_is_black(images[name]) for name in ("normal", "response_only", "background", "label_id")):
            raise ValueError(f"{state}: substituted all-black rendered layer")
        if not image_is_black(images["label_id_background"]):
            raise ValueError(f"{state}: label ID background is not black")
        if not grayscale_identity_pass(images["label_id"]):
            raise ValueError(f"{state}: label ID pass is not contrast-safe grayscale")

        label_mask = difference_mask(images["label_id"], images["label_id_background"])
        response_mask = difference_mask(images["response_only"], images["background"])
        label_box = mask_bbox(label_mask)
        response_box = mask_bbox(response_mask)
        if not label_box or not response_box:
            raise ValueError(f"{state}: empty rendered mask")
        readability = record.get("projected_readability", {})
        if (not close_list(readability.get("frame_rect"), expected_frame)
                or not finite_number(readability.get("required_clearance_px"))
                or not math.isclose(float(readability["required_clearance_px"]), required_logical,
                                    rel_tol=0.0, abs_tol=1e-5)):
            raise ValueError(f"{state}: candidate-authored threshold/frame differs from independent contract")
        width, height = expected_capture_size
        scale_x = width / float(logical_size[0])
        scale_y = height / float(logical_size[1])
        radius_x = int(math.ceil(required_logical * scale_x))
        radius_y = int(math.ceil(required_logical * scale_y))
        square_radius = max(radius_x, radius_y)
        safe_frame = [
            int(math.ceil(expected_frame[0] * scale_x)),
            int(math.ceil(expected_frame[1] * scale_y)),
            int(math.floor((expected_frame[0] + expected_frame[2]) * scale_x)),
            int(math.floor((expected_frame[1] + expected_frame[3]) * scale_y)),
        ]
        safe_frame_passed = (label_box[0] >= safe_frame[0] and label_box[1] >= safe_frame[1]
                             and label_box[2] <= safe_frame[2] and label_box[3] <= safe_frame[3])
        direct = ImageChops.multiply(label_mask, response_mask)
        dilated_response = dilate_square(response_mask, square_radius)
        clearance_violation = ImageChops.multiply(label_mask, dilated_response)
        direct_pixels = count_mask(direct)
        clearance_pixels = count_mask(clearance_violation)

        prefix = f"{state}-{angle}"
        mask_paths = {
            "label": masks_root / f"{prefix}-label-mask.png",
            "response": masks_root / f"{prefix}-response-mask.png",
            "dilated_response": masks_root / f"{prefix}-dilated-response-mask.png",
            "violation": masks_root / f"{prefix}-violation-mask.png",
        }
        for image, path in ((label_mask, mask_paths["label"]), (response_mask, mask_paths["response"]),
                            (dilated_response, mask_paths["dilated_response"]),
                            (clearance_violation, mask_paths["violation"])):
            image.save(path)
        clearance_passed = clearance_pixels == 0
        rows.append({
            "state": state, "angle": angle, "case_nonce": nonce,
            "case_core_sha256": next(iter(independent_core_hashes)),
            "source_files": {name: path.name for name, path in paths.items()},
            "source_sha256": {name: sha256(path) for name, path in paths.items()},
            "source_files_bound": True, "size": [width, height],
            "difference_threshold": PIXEL_THRESHOLD,
            "label_mask_pixels": count_mask(label_mask), "response_mask_pixels": count_mask(response_mask),
            "label_bbox": label_box, "response_bbox": response_box,
            "safe_frame_physical": safe_frame, "safe_frame_passed": safe_frame_passed,
            "required_clearance_logical_px": required_logical,
            "physical_scale_xy": [scale_x, scale_y],
            "required_clearance_radius_xy": [radius_x, radius_y],
            "conservative_square_dilation_radius": square_radius,
            "minimum_observed_bbox_clearance_physical_px": bbox_clearance(label_box, response_box),
            "direct_overlap_pixels": direct_pixels,
            "dilated_clearance_violation_pixels": clearance_pixels,
            "direct_overlap": direct_pixels > 0, "clearance_passed": clearance_passed,
            "passed": safe_frame_passed and clearance_passed,
            "mask_files": {name: path.name for name, path in mask_paths.items()},
            "mask_sha256": {name: sha256(path) for name, path in mask_paths.items()},
        })

    rows.sort(key=lambda row: STATES.index(row["state"]))
    direct_failures = [row["state"] for row in rows if row["direct_overlap"]]
    clearance_failures = [row["state"] for row in rows if not row["clearance_passed"]]
    safe_frame_failures = [row["state"] for row in rows if not row["safe_frame_passed"]]
    failed_states = [row["state"] for row in rows if not row["passed"]]
    report = {
        "contract": CONTRACT, "domain_complete": False, "variant": variant,
        "source": source, "product_blob_sha256": product_blob_sha256,
        "probe_source": probe_source, "capture_sha256": capture_sha256,
        "verifier_sha256": verifier_sha256, "workflow_sha256": workflow_sha256,
        "resource_symbols_sha256": resource_symbols_sha256,
        "manifest": str(manifest_path), "manifest_sha256": sha256(manifest_path),
        "mask_construction": "label=LI-LB;response=R-B;normal=N",
        "label_id_contract": "full nonzero grayscale glyph and outline on black; floor, caption and response hidden",
        "contrast_safe_label_coverage": True, "mask_independent_of_analytic_label_rect": True,
        "threshold_source": "independent constants matching product contract",
        "dilation_semantics": "conservative square dilation using max(ceil(logical*x_scale), ceil(logical*y_scale))",
        "state_count": 6, "case_count": 6,
        "direct_failure_states": direct_failures, "clearance_failure_states": clearance_failures,
        "safe_frame_failure_states": safe_frame_failures, "failed_states": failed_states,
        "direct_failure_count": len(direct_failures), "failure_count": len(failed_states),
        "known_failed_states_rediscovered": sorted(set(KNOWN_FAILED_STATES).intersection(direct_failures)),
        "rows": rows, "task_approved": False,
    }
    errors = report_errors(report, expect_variant=variant)
    report["errors"] = errors
    report["passed"] = not errors
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--masks", required=True, type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--product-blob-sha256", required=True)
    parser.add_argument("--variant", choices=("baseline", "candidate"), required=True)
    parser.add_argument("--probe-source", required=True)
    parser.add_argument("--capture-sha256", required=True)
    parser.add_argument("--verifier-sha256", required=True)
    parser.add_argument("--workflow-sha256", required=True)
    parser.add_argument("--resource-symbols-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.root, args.manifest, args.masks, args.source,
                    args.product_blob_sha256, args.variant, args.probe_source,
                    args.capture_sha256, args.verifier_sha256, args.workflow_sha256,
                    args.resource_symbols_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "contract", "domain_complete", "variant", "source", "direct_failure_states",
        "clearance_failure_states", "safe_frame_failure_states", "passed", "errors"
    )}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
