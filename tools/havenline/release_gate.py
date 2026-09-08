#!/usr/bin/env python3
"""Fail-closed release-evidence validator. Does not run QA or create approvals.

Raw artifacts must be source/APK-bound. This checks recorded evidence and metrics,
not the honesty of its producer; provenance still needs an independently trusted
runner. Synthetic/unit-test results never certify the actual game.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Any

VIEWS = (
    'mobile-render', 'mobile-rear', 'mobile-side', 'mobile-left',
    'mobile-three-quarter', 'outpost-night', 'outpost-blizzard',
    'outpost-warmth4', 'outpost-gather', 'outpost-shelter-detail',
    'outpost-shelter-detail-rear', 'outpost-furnace-detail',
    'outpost-tree-detail', 'outpost-native-4k',
)
DIMENSIONS = ('craft', 'materials', 'lighting', 'composition', 'integrity', 'evidence')
DEVICE_CASES = ('phone', 'tablet_standard', 'tablet_large', 'fold_outer', 'fold_inner')
FUNCTIONS = ('launch', 'touch_movement', 'safe_area', 'menu_scroll', 'save_reload',
             'pause_resume', 'screen_resize', 'full_game_load')
REQUIRED_GAME_CHECKS = ('reference_video_fidelity_10_of_10', 'native_arm64_build', 'android_install_launch_lifecycle', 'opening_gameplay_rendered_end_to_end', 'four_character_identities_human_approved', 'all_character_motion_sets', 'whole_rig_critic_at_least_9', 'non_primitive_environment_human_approved', 'wolf_and_additional_survivor_art', 'production_chains_and_worker_jobs', 'ten_connected_biomes_and_transport', 'weather_and_day_night', 'google_identity_and_cloud_save', 'safe_area_and_fold_lifecycle', 'sustained_physical_4k_60', 'audio_and_feedback_complete', 'customer_survivor_pet_authored_models', 'population_gameplay_and_save_regression', 'npc_role_animations_and_visual_variants', 'independent_critic_strictly_above_9', 'phone_and_tablet_automatic_layout', 'phone_and_tablet_full_functionality', 'environment_independent_critic_10_of_10', 'native_4k60_physical_phone_and_tablet')
SHA = re.compile(r'^[0-9a-f]{64}$')
COMMIT = re.compile(r'^[0-9a-f]{40}$')


def number(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError('Boolean is not a measurement')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Non-finite measurement')
    return result


def artifact(root: Path, spec: Any) -> bytes:
    if not isinstance(spec, dict) or not isinstance(spec.get('path'), str):
        raise ValueError('Missing artifact reference')
    expected = spec.get('sha256', '')
    if not SHA.fullmatch(expected):
        raise ValueError('Missing SHA256')
    relative = Path(spec['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Artifact path escapes evidence directory')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing artifact or escaped symlink')
    if path.stat().st_size > 512 * 1024 * 1024:
        raise ValueError('Evidence file exceeds size limit')
    data = path.read_bytes()
    if not data or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Empty or changed artifact')
    return data


def measure_presentations(data: bytes) -> dict:
    intervals: list[float] = []
    first = previous = None
    for row in csv.DictReader(io.StringIO(data.decode('utf-8'))):
        # Integer nanoseconds avoid floating-point loss on absolute timestamps.
        tick = int(row['presentation_ns'])
        if tick < 0 or (previous is not None and tick <= previous):
            raise ValueError('Presentation timestamps are not strictly increasing')
        if int(row['internal_width']) < 3840 or int(row['internal_height']) < 2160:
            raise ValueError('Internal framebuffer fell below native 4K dimensions')
        if number(row['render_scale']) != 1.0:
            raise ValueError('Render scaling is not native 1.0')
        if first is None:
            first = tick
        if previous is not None:
            intervals.append((tick - previous) / 1e6)
        previous = tick
    if not intervals:
        raise ValueError('No measured presented-frame intervals')
    duration = (previous - first) / 1e9
    sorted_ms = sorted(intervals)
    p99 = sorted_ms[math.ceil(len(sorted_ms) * .99) - 1]
    rate = len(intervals) / duration
    if duration < 1800:
        raise ValueError('Fewer than 30 sustained measured minutes')
    if rate < 60 or p99 > 16.667:
        raise ValueError('Presented-frame rate/pacing does not meet 60 FPS')
    if max(intervals) > 33.334:
        raise ValueError('Presented-frame trace contains a visible long-frame hitch')
    return {'duration_seconds': duration, 'intervals': len(intervals),
            'average_presented_fps': rate, 'p99_ms': p99, 'maximum_ms': max(intervals)}


def check_thermal(data: bytes, duration: float) -> None:
    values = json.loads(data)
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError('Missing thermal time series')
    previous = None
    for sample in values:
        second = number(sample['elapsed_seconds'])
        status = number(sample['android_thermal_status'])
        if second < 0 or status not in (0, 1, 2):
            raise ValueError('Invalid, unknown or severe thermal status')
        if previous is None and second > 1:
            raise ValueError('Thermal trace missing session start')
        if previous is not None and not 0 < second - previous <= 5:
            raise ValueError('Non-monotonic or incomplete thermal trace')
        previous = second
    if previous < duration - 1:
        raise ValueError('Thermal trace does not cover the full performance session')


def validate(root: Path, source: str, status: dict) -> dict:
    errors: list[str] = []
    metrics: dict = {}
    def attempt(label, operation):
        try:
            return operation()
        except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError) as exc:
            errors.append(f'{label}: {exc}')
            return None

    if not COMMIT.fullmatch(source):
        errors.append('Expected source must be an exact 40-character Git commit')
    requirements = status.get('required', {})
    if isinstance(requirements, dict):
        for missing in sorted(set(REQUIRED_GAME_CHECKS) - set(requirements)):
            errors.append(f'Complete game requirement missing: {missing}')
    if not isinstance(requirements, dict) or not requirements:
        errors.append('Complete game requirements are absent')
    else:
        for key, state in requirements.items():
            if state != 'PASS_VERIFIED':
                errors.append(f'Full-game requirement {key}: {state}')
    manifest = attempt('Release evidence', lambda: json.loads((root/'release-evidence.json').read_text()))
    if not isinstance(manifest, dict):
        return {'passed':False, 'source_sha':source, 'errors':errors or ['Invalid manifest'], 'device_metrics':{}}
    if manifest.get('source_sha') != source:
        errors.append('Evidence is stale or belongs to another source revision')
    if manifest.get('evidence_origin') != 'independently_executed':
        errors.append('Evidence is not independently executed hardware/critic output')
    apk = attempt('Exact APK', lambda: artifact(root, manifest['apk']))
    apk_hash = hashlib.sha256(apk).hexdigest() if apk else None
    if not apk_hash:
        errors.append('No exact APK binding')
    def binding(record):
        if record.get('source_sha') != source or record.get('apk_sha256') != apk_hash:
            raise ValueError('Record does not match the tested source/APK')
    environment = manifest.get('environment', {})
    attempt('Visual source binding', lambda: binding(environment))
    if environment.get('independent_critic_executed') is not True:
        errors.append('Separate critic execution is not established')
    if environment.get('primitive_placeholders_remaining') != 0 or isinstance(environment.get('primitive_placeholders_remaining'), bool):
        errors.append('Zero unfinished/primitive-looking assets is not established')
    if environment.get('unresolved_defects') != []:
        errors.append('Visual defects are unresolved or unreported')
    attempt('Raw independent execution', lambda: artifact(root, environment['execution_record']))
    views = environment.get('views', [])
    if not isinstance(views, list):
        views = []
    names = [r.get('view') for r in views if isinstance(r, dict)]
    if len(names) != len(VIEWS) or set(names) != set(VIEWS):
        errors.append('Fourteen unique required actual-render views are not fully reviewed')
    image_hashes = set()
    for record in views:
        def review(r=record):
            binding(r)
            scores = r['scores']
            if set(scores) != set(DIMENSIONS) or any(number(v) != 10 for v in scores.values()):
                raise ValueError('Every required visual dimension must be exactly 10/10')
            if r.get('defects') != [] or r.get('review_complete') is not True:
                raise ValueError('Incomplete or failed view review')
            image = artifact(root, r['capture'])
            if not image.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Capture is not an actual PNG artifact')
            image_hashes.add(hashlib.sha256(image).hexdigest())
            artifact(root, r['raw_critic_response'])
        attempt('Visual view', review)
    if len(image_hashes) != len(VIEWS):
        errors.append('Missing or duplicated multi-angle image evidence')
    trace_hashes: set[str] = set()
    devices = manifest.get('devices', [])
    if not isinstance(devices, list):
        devices = []
    cases = [d.get('case') for d in devices if isinstance(d, dict)]
    if len(cases) != len(DEVICE_CASES) or set(cases) != set(DEVICE_CASES):
        errors.append('Phone, both tablet test classes and both fold states require separate evidence')
    for device in devices:
        def hardware(d=device):
            binding(d)
            if d.get('platform') != 'Android' or d.get('physical_device') is not True:
                raise ValueError('Emulator/desktop output cannot certify Android performance')
            for key in ('model', 'android_version', 'gpu', 'runner_id', 'presentation_trace_source'):
                if not isinstance(d.get(key), str) or not d[key].strip():
                    raise ValueError(f'Missing hardware/provenance field: {key}')
            if d.get('presentation_trace_source') not in ('android_frame_timeline', 'surfaceflinger'):
                raise ValueError('Engine-submission counters are not display-presentation evidence')
            if d.get('fixed_timestep_used') is not False or d.get('upscaling_used') is not False:
                raise ValueError('Synthetic timing/upscaled rendering cannot pass')
            if d.get('workload') != 'complete_game_worst_case' or d.get('interruptions') != 0:
                raise ValueError('Incomplete workload or interrupted sustained run')
            if number(d.get('warmup_seconds', 0)) < 60:
                raise ValueError('Pre-measurement warmup is missing')
            raw_trace = artifact(root, d['raw_platform_trace'])
            trace_hashes.add(hashlib.sha256(raw_trace).hexdigest())
            result = measure_presentations(artifact(root, d['presented_frames_csv']))
            check_thermal(artifact(root, d['thermal_series_json']), result['duration_seconds'])
            checks = d.get('functional_checks', {})
            expected = set(FUNCTIONS) | ({'fold_unfold_continuity'} if d['case'].startswith('fold_') else set())
            if set(checks) != expected:
                raise ValueError('Missing or unexpected device functional checks')
            for name, check in checks.items():
                if check.get('result') != 'PASS_VERIFIED':
                    raise ValueError(f'Unverified device check: {name}')
                artifact(root, check['evidence'])
            metrics[d['case']] = result
        attempt('Physical device', hardware)
    if len(trace_hashes) != len(DEVICE_CASES):
        errors.append('Distinct physical test runs are not established for every device case')
    return {'passed':not errors, 'source_sha':source, 'apk_sha256':apk_hash,
            'errors':errors, 'device_metrics':metrics,
            'limitations':['Validates supplied records, hashes and measurements; does not create independent reviews or authenticate a dishonest evidence producer.',
                           'No universal all-Android hardware promise. Only explicitly tested configurations may be certified.']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--status', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = validate(args.evidence, args.source, json.loads(args.status.read_text()))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        report = {'passed':False, 'errors':[str(exc)]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
