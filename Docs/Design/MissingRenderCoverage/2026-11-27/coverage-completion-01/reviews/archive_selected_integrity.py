"""Independent, read-only evidence check for a supplied Havenline selection.

This does not grant visual approval, assemble files, or publish anything.
Existing independent visual judgments are checked for exact artifact bindings.
"""
from pathlib import Path
from functools import lru_cache
import argparse
import datetime
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def locate(value):
    p = Path(value)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == ROOT.name:
        return ROOT.parent / p
    return ROOT / p


@lru_cache(maxsize=4096)
def metrics(value):
    p = locate(value)
    data = p.read_bytes()
    return {'path': str(p), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob_sha': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


@lru_cache(maxsize=6)
def pixels(value):
    with Image.open(locate(value)) as im:
        return im.convert('RGBA')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--selection', default='selection-working.json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    selection_path = locate(args.selection)
    selection_bytes = selection_path.read_bytes()
    selection = json.loads(selection_bytes)
    required = json.loads((ROOT / 'requirements.json').read_text())
    expected = {sheet: family['id'] for family in required['families'] for sheet in family['required_sheets']}
    errors, results, ids = [], [], []
    total_crops = 0

    for selected in selection['selected']:
        rid = selected.get('render_id') or selected['id']
        deliverable = selected.get('deliverable_id', rid)
        ids.append(deliverable)
        local_errors = []
        def need(value, message):
            if not value:
                local_errors.append(message)
        def bound(binding):
            path = binding.get('path') or binding.get('local_path') or binding.get('source_path')
            observed = metrics(path)
            need(observed['sha256'] == binding['sha256'], 'Bound file hash differs: ' + str(path))
            if 'bytes' in binding:
                need(observed['bytes'] == binding['bytes'], 'Bound file size differs: ' + str(path))
            return locate(path)

        try:
            image_path = selected.get('local_path') or str(ROOT / 'renders' / (rid + '.png'))
            im_metrics = metrics(image_path)
            need(im_metrics['sha256'] == selected['sha256'], 'Selected image hash differs')
            need(im_metrics['bytes'] == selected['bytes'], 'Selected image size differs')
            need(deliverable in expected, 'Unknown deliverable identity')
            if 'family_id' in selected:
                need(expected.get(deliverable) == selected['family_id'], 'Family identity differs')
            report_path = selected.get('review_path') or selected.get('review')
            report_metrics = metrics(report_path)
            need(report_metrics['sha256'] == selected['review_sha256'], 'Selected review hash differs')
            review = json.loads(locate(report_path).read_text())
            need(review.get('independent') is True, 'Review is not marked independent')
            need(review.get('reviewer') in {'/root/missing_cast_critic', '/root/missing_world_audit'}, 'Unexpected reviewer identity')
            need(str(review.get('status', '')).startswith('PASS'), 'Review status is not PASS')
            need(review.get('score', 0) > 9.0, 'Review score does not exceed 9.0')
            need(review.get('score') == selected['score'], 'Selected score differs from review')
            need(review.get('all_mandatory_visual_checks_passed') is True, 'Mandatory visual checks not all passed')
            need(not review.get('mandatory_defects_remaining'), 'Mandatory defects remain')
            need(not review.get('approval_reopened') and not review.get('approval_invalidated'), 'Approval is reopened or invalidated')
            need(review.get('actual_full_native_png_inspected') is True or review.get('actual_full_png_inspected') is True, 'Missing native full-image inspection evidence')
            need(bool(review.get('areas')), 'No individual scored mandatory areas')
            for area in review.get('areas', []):
                need(area.get('score', 0) > 9.0 and str(area.get('status', '')).startswith('PASS'), 'Mandatory area failed: ' + str(area.get('id')))
            rimage = review['reviewed_image']
            need(rimage.get('sha256', rimage.get('source_sha256')) == im_metrics['sha256'], 'Reviewed image hash differs')
            need(rimage.get('bytes', rimage.get('source_bytes')) == im_metrics['bytes'], 'Reviewed image size differs')
            provenance_bindings = review.get('crop_provenance', [])
            if isinstance(provenance_bindings, dict):
                provenance_bindings = [provenance_bindings]
            need(bool(provenance_bindings), 'No crop provenance bindings')
            crop_records = []
            crop_names = set()
            for binding in provenance_bindings:
                provenance_path = bound(binding)
                provenance = json.loads(provenance_path.read_text())
                if isinstance(provenance, list):
                    crop_rows, default_source, default_sha = provenance, None, None
                else:
                    crop_rows = provenance.get('crops') or provenance['native_crops']
                    default_source = provenance.get('source_path') or provenance.get('source')
                    default_sha = provenance.get('source_sha256')
                    if isinstance(default_source, dict):
                        default_sha = default_source['sha256']
                        default_source = default_source['path']
                for crop in crop_rows:
                    source_binding = crop.get('source') or {}
                    if isinstance(source_binding, str):
                        source_binding = {'path': source_binding}
                    output_binding = crop.get('output') or {}
                    source_path = crop.get('source_path') or source_binding.get('path') or default_source
                    source_sha = crop.get('source_sha256') or source_binding.get('sha256') or default_sha
                    crop_path = crop.get('path') or crop.get('output_path') or output_binding.get('path')
                    crop_sha = crop.get('sha256') or crop.get('output_sha256') or output_binding.get('sha256')
                    box = crop.get('box') or crop.get('crop_box_xyxy') or crop.get('bbox_xyxy') or crop.get('bbox')
                    need(metrics(source_path)['sha256'] == source_sha, 'Crop source hash differs: ' + str(source_path))
                    need(metrics(crop_path)['sha256'] == crop_sha, 'Crop output hash differs: ' + str(crop_path))
                    wanted = pixels(source_path).crop(tuple(box))
                    got = pixels(crop_path)
                    need(got.size == wanted.size and got.tobytes() == wanted.tobytes(), 'Crop pixels differ from native source: ' + str(crop_path))
                    crop_names.update({str(crop.get('id', '')), str(crop.get('name', '')), Path(crop_path).name, str(locate(crop_path))})
                    crop_records.append({'path': str(locate(crop_path)), 'sha256': crop_sha, 'native_source_sha256': source_sha, 'box_xyxy': box})
            inspected = review.get('actual_native_crops_inspected', [])
            need(bool(inspected), 'No inspected native closeups listed')
            for crop in inspected:
                if isinstance(crop, dict):
                    path = bound(crop)
                    need(str(path) in crop_names or path.name in crop_names, 'Inspected crop lacks pixel provenance: ' + str(path))
                else:
                    need(crop in crop_names or Path(crop).name in crop_names, 'Inspected crop lacks pixel provenance: ' + str(crop))
            total_crops += len(crop_records)
            results.append({'deliverable_id': deliverable, 'render_id': rid, 'reviewer': review.get('reviewer'),
                            'selected_image': im_metrics, 'review': report_metrics, 'score': review.get('score'),
                            'mandatory_area_count': len(review.get('areas', [])), 'native_crops': crop_records,
                            'status': 'PASS_BINDINGS_AND_NATIVE_CROP_PIXELS' if not local_errors else 'FAIL', 'issues': local_errors})
        except Exception as exc:
            local_errors.append(type(exc).__name__ + ': ' + str(exc))
        errors.extend({'render_id': rid, 'issue': issue} for issue in local_errors)

    if len(ids) != len(set(ids)):
        errors.append({'issue': 'Duplicate deliverable identities'})
    if any(i not in expected for i in ids):
        errors.append({'issue': 'Unexpected deliverable identities'})
    pending = sorted(set(expected) - set(ids))
    result = {
        'schema_version': 1, 'reviewer': '/root/missing_cast_critic', 'independent': True,
        'reviewed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'PASS_SELECTED_EVIDENCE_INTEGRITY_ONLY' if not errors else 'FAIL_SELECTED_EVIDENCE_INTEGRITY',
        'scope': 'Exact independent visual-review bindings and native crop pixel integrity. Does not replace visual criticism, final archive content/package gates or remote publication verification.',
        'selection_binding': {'path': str(selection_path), 'bytes': len(selection_bytes), 'sha256': hashlib.sha256(selection_bytes).hexdigest()},
        'required_sheet_count': len(expected), 'required_family_count': len(required['families']),
        'selected_count': len(ids), 'pending_deliverables': pending, 'verified_native_crop_count': total_crops,
        'selection_complete': not pending and not errors, 'issues': errors, 'results': results,
        'publication_approved': False,
    }
    output = locate(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'results'}))


if __name__ == '__main__':
    main()
