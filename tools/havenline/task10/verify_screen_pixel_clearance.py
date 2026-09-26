#!/usr/bin/env python3
"""Verify the T10 representative label/response probe from retained rasters."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

CONTRACT = "T10_RENDERED_SCREEN_PIXEL_CLEARANCE_V3"
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


CAMERA_FOV = {"front":44.0, "side":44.0, "three-quarter":44.0, "overhead":40.0, "gameplay":48.0, "detail":40.0}
DEVICES = {"phone_16_9":(2400,1080), "phone_20_9":(2400,1080), "tablet_16_10":(2560,1600), "tablet_4_3":(2732,2048), "foldable_outer":(2520,1080), "foldable_inner":(2208,1768)}
PROFILES = {f"{device}__{scale}": (size,size,scale) for device,size in DEVICES.items() for scale in (1.0,0.85,1.35)}
PROFILES["native4k_anchors"] = ((1920,1080),(3840,2160),1.0)
PROFILES["native4k_full"] = ((1920,1080),(3840,2160),1.0)

def profile_cases(profile):
    return ({("ready","overhead"),("blocked","overhead")} if profile == "native4k_anchors"
            else {(state,angle) for state in STATES for angle in CAMERA_FOV})

def normal_correspondence(normal, response, label_mask, response_mask):
    # N and R can differ by one code value on response faces when the label
    # draw submission changes (observed in both V2 subjects). Bound that
    # quantization spatially and numerically; never relax the collision masks.
    delta = difference_mask(normal, response)
    label_support = dilate_square(label_mask, 1)
    outside = ImageChops.multiply(delta, ImageChops.invert(label_support))
    outside_array = np.asarray(outside) != 0
    response_support = np.asarray(dilate_square(response_mask, 1)) != 0
    channel_delta = np.abs(np.asarray(normal.convert("RGB"), dtype=np.int16)
                           - np.asarray(response.convert("RGB"), dtype=np.int16)).max(axis=2)
    unexpected = int(np.count_nonzero(outside_array & (~response_support | (channel_delta > 1))))
    inside = count_mask(ImageChops.multiply(delta, label_mask))
    coverage = inside / max(1, count_mask(label_mask))
    return {"unexpected_outside_label_pixels":unexpected,
            "response_quantization_pixels":int(np.count_nonzero(outside_array & response_support & (channel_delta == 1))),
            "label_coverage":coverage, "passed":unexpected == 0 and coverage >= 0.5}


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


def expected_layer_name(state: str, layer: str, angle: str) -> str:
    suffix = {
        "normal": "",
        "response_only": "-response-only",
        "background": "-background",
        "label_id_background": "-label-id-background",
        "label_id": "-label-id",
    }[layer]
    return f"{state}-{angle}{suffix}.png"


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


def serialized_frame(logical_size: list[int]) -> list[float]:
    # Godot Rect2/Vector2 stores each intermediate as IEEE754 binary32.
    # Keep expected_geometry's ideal double frame for physical raster thresholds.
    def f32(value):
        return struct.unpack("<f", struct.pack("<f", value))[0]
    _, ideal = expected_geometry(logical_size)
    inset = f32(ideal[0])
    doubled = f32(inset * 2.0)
    return [inset, inset, f32(float(logical_size[0]) - doubled),
            f32(float(logical_size[1]) - doubled)]


def close_list(actual, expected, tolerance=1e-5) -> bool:
    return (isinstance(actual, list) and len(actual) == len(expected)
            and all(finite_number(a) and math.isclose(float(a), float(e), rel_tol=0.0, abs_tol=tolerance)
                    for a, e in zip(actual, expected)))


def nominal_screen_unit_scale(core: dict, logical_size: list[int]) -> float:
    camera=core["camera_transform"]
    label=core["label_transform"]
    basis=np.array([camera[k] for k in ("basis_x","basis_y","basis_z")],dtype=float).T
    if not np.allclose(basis.T@basis,np.eye(3),rtol=0,atol=1e-5):
        raise ValueError("camera basis must be orthonormal")
    camera_position=np.linalg.solve(basis,np.array(label["origin"])-np.array(camera["origin"]))
    depth=-float(camera_position[2])
    if not float(core["camera_near"]) < depth < float(core["camera_far"]):
        raise ValueError("label depth outside camera frustum")
    label_basis=np.array([label[k] for k in ("basis_x","basis_y","basis_z")],dtype=float).T
    lengths=[float(np.linalg.norm(label[k])) for k in ("basis_x","basis_y","basis_z")]
    if min(lengths)<=0 or np.linalg.det(label_basis)<=0 or not np.allclose(label_basis.T@label_basis,np.eye(3)*lengths[0]**2,rtol=0,atol=1e-5):
        raise ValueError("label basis must have positive uniform scale")
    keep=core["camera_keep_aspect"]
    if type(keep) is not int or keep not in (0,1):raise ValueError("invalid camera keep aspect")
    extent=logical_size[1] if keep==1 else logical_size[0]
    focal=float(extent)/(2.0*math.tan(math.radians(float(core["camera_fov"]))*0.5))
    return float(core["label_realization"]["pixel_size"])*lengths[0]*focal/depth


def validate_screen_font_size(core: dict, logical_size: list[int]) -> None:
    if core.get("lifecycle_descriptor",{}).get("label_layout_policy")!="constrained_screen_pixels_v3" or core.get("lifecycle_descriptor",{}).get("label_size_coordinate_space")!="logical_viewport_pixels":
        raise ValueError("missing versioned screen-pixel contract")
    requested=core.get("evidence_scale")
    if not finite_number(requested) or not 0.85<=float(requested)<=1.35:
        raise ValueError("invalid requested readability")
    realized=nominal_screen_unit_scale(core,logical_size)
    if not math.isfinite(realized) or not 0.8499*float(requested)<=realized<=1.0001*float(requested):
        raise ValueError("projected font size violates protected fit range")


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
    if (not finite_number(core.get("camera_fov")) or not math.isclose(float(core["camera_fov"]), CAMERA_FOV[angle])
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
            or float(realization["pixel_size"]) <= 0.0
            or realization.get("billboard") != 1 or realization.get("no_depth_test") is not True
            or realization.get("render_priority") != 100
            or realization.get("outline_render_priority") != 99):
        raise ValueError(f"{state}: incomplete Label3D realization binding")
    validate_screen_font_size(core,logical_size)
    font = core.get("font_identity")
    version = font.get("engine_version", {}) if isinstance(font, dict) else {}
    if (not isinstance(font, dict) or not font.get("class") or font.get("fallback_count") != 1
            or font.get("font_size") != 38 or font.get("outline_size") != 9
            or font.get("resource_symbols_path") != "res://assets/world_transform_v1/resource_symbols.tres"
            or font.get("resource_symbols_sha256") != resource_symbols_sha256
            or not isinstance(version, dict) or [version.get(k) for k in ("major", "minor", "patch")] != [4, 7, 2]):
        raise ValueError(f"{state}: missing font/resource identity")



def verify(root: Path, manifest_path: Path, masks_root: Path, source: str,
           product_blob_sha256: str, variant: str, probe_source: str,
           capture_sha256: str, verifier_sha256: str, workflow_sha256: str,
           resource_symbols_sha256: str,
           profile: str, *, reanalysis_verifier_sha256: str | None = None) -> dict:
    geometry = PROFILES[profile]
    logical_expected, expected_capture_size, scale = geometry
    expected_cases = profile_cases(profile)
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
    executing_sha256 = reanalysis_verifier_sha256 or verifier_sha256
    if sha256(Path(__file__)) != executing_sha256:
        raise ValueError("running verifier does not match bound verifier hash")
    if manifest.get("rendered_clearance_probe") is not True or manifest.get("domain_profile") != profile:
        raise ValueError("manifest has the wrong domain profile")
    if manifest.get("evidence_scale") != scale:
        raise ValueError("wrong readability endpoint")
    logical_size = manifest.get("logical_size")
    if (not isinstance(logical_size, list) or len(logical_size) != 2
            or not all(isinstance(value, int) and value > 0 for value in logical_size)):
        raise ValueError("invalid logical viewport")
    if logical_size != list(logical_expected):
        raise ValueError("logical viewport differs from independent profile")
    capture_size = manifest.get("capture_resolution")
    if capture_size != list(expected_capture_size):
        raise ValueError("physical capture resolution is not the independently expected size")
    if manifest.get("native_scale_1") is not (tuple(expected_capture_size) == EXPECTED_CAPTURE_SIZE):
        raise ValueError("native-scale claim does not match expected capture")
    renderer = manifest.get("renderer")
    if not isinstance(renderer, str) or not renderer.startswith("mobile/"):
        raise ValueError("unexpected manifest renderer")
    records = manifest.get("records", [])
    if len(records) != len(expected_cases) or {(r.get("state"), r.get("angle")) for r in records} != expected_cases:
        raise ValueError("profile requires its exact complete case set")

    masks_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    seen_nonces: set[str] = set()
    seen_paths: set[Path] = set()
    required_logical, expected_frame = expected_geometry(logical_size)
    for record in records:
        state = record.get("state")
        angle = record.get("angle")
        if (state, angle) not in expected_cases:
            raise ValueError("unexpected state/angle record")
        layers = record.get("rendered_clearance_layers", {})
        layer_records = layers.get("layer_records", {})
        if set(layer_records) != set(LAYER_NAMES) or layers.get("process_frozen") is not True:
            raise ValueError(f"{state}: incomplete frozen layer records")
        nonce = layers.get("case_nonce")
        expected_nonce = hashlib.sha256(f"{source}:{probe_source}:{state}:{angle}:{profile}".encode()).hexdigest()
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
            if layer.get("file") != expected_layer_name(state, layer_name, angle):
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
            if core.get("domain_profile") != profile or core.get("evidence_scale") != scale:
                raise ValueError("layer profile/scale mismatch")
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
        if any(image_is_black(images[name]) for name in ("normal", "response_only", "background")):
            raise ValueError(f"{state}: substituted all-black rendered layer")
        if not image_is_black(images["label_id_background"]):
            raise ValueError(f"{state}: label ID background is not black")
        if not grayscale_identity_pass(images["label_id"]):
            raise ValueError(f"{state}: label ID pass is not contrast-safe grayscale")

        label_mask = difference_mask(images["label_id"], images["label_id_background"])
        response_mask = difference_mask(images["response_only"], images["background"])
        label_box = mask_bbox(label_mask)
        response_box = mask_bbox(response_mask)
        masks_nonempty = bool(label_box and response_box)
        # An entirely offscreen label is still a measured geometry failure.
        # Preserve its empty mask and continue collecting the other cases.
        label_box = label_box or [0, 0, 0, 0]
        response_box = response_box or [0, 0, 0, 0]
        readability = record.get("projected_readability", {})
        if (not close_list(readability.get("frame_rect"), serialized_frame(logical_size))
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
        correspondence = normal_correspondence(images["normal"], images["response_only"], label_mask, response_mask)
        analytic_passed = readability.get("passed") is True and readability.get("placement_found") is True
        rows.append({
            "profile": profile, "evidence_scale": scale, "state": state, "angle": angle, "case_nonce": nonce,
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
            "normal_correspondence": correspondence, "analytic_passed": analytic_passed,
            "passed": masks_nonempty and safe_frame_passed and clearance_passed and correspondence["passed"] and analytic_passed,
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
        "profile": profile, "evidence_scale": scale, "case_count": len(expected_cases),
        "direct_failure_states": direct_failures, "clearance_failure_states": clearance_failures,
        "safe_frame_failure_states": safe_frame_failures, "failed_states": failed_states,
        "direct_failure_count": len(direct_failures), "failure_count": len(failed_states),
        "known_failed_states_rediscovered": sorted(set(KNOWN_FAILED_STATES).intersection(direct_failures)),
        "rows": rows, "task_approved": False,
    }
    # Geometry failures are outcomes, never reasons to discard other valid cases.
    errors = ["one or more case checks failed"] if failed_states else []
    if manifest.get("passed") is not True:
        errors.append("capture manifest reports a failure")
    report["errors"] = errors
    report["passed"] = not errors
    if reanalysis_verifier_sha256 is not None:
        report["derivative_reanalysis"] = {
            "capture_verifier_sha256": verifier_sha256,
            "executing_verifier_sha256": executing_sha256,
            "original_evidence_unchanged": True,
            "task_approved": False,
        }
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
    parser.add_argument("--profile", required=True, choices=tuple(PROFILES))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.root, args.manifest, args.masks, args.source,
                    args.product_blob_sha256, args.variant, args.probe_source,
                    args.capture_sha256, args.verifier_sha256, args.workflow_sha256,
                    args.resource_symbols_sha256, args.profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "contract", "domain_complete", "variant", "source", "direct_failure_states",
        "clearance_failure_states", "safe_frame_failure_states", "passed", "errors"
    )}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
