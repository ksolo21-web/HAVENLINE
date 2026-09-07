"""Inspect the exported APK itself; source configuration is not export evidence.

Signature verification is performed separately by Android SDK apksigner in CI.
This parser only reads the binary manifest and checks packaging invariants.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile


def manifest_elements(data: bytes) -> list[dict]:
    if len(data) < 8 or struct.unpack_from('<H', data)[0] != 3:
        raise ValueError('Expected Android binary XML')
    strings: list[str] = []
    elements: list[dict] = []
    offset = 8

    def length_at(position: int, utf8: bool) -> tuple[int, int]:
        if utf8:
            value = data[position]
            position += 1
            if value & 0x80:
                value = ((value & 0x7f) << 8) | data[position]
                position += 1
        else:
            value = struct.unpack_from('<H', data, position)[0]
            position += 2
            if value & 0x8000:
                value = ((value & 0x7fff) << 16) | struct.unpack_from('<H', data, position)[0]
                position += 2
        return value, position

    while offset + 8 <= len(data):
        kind, header_size, chunk_size = struct.unpack_from('<HHI', data, offset)
        if header_size < 8 or chunk_size < header_size or offset + chunk_size > len(data):
            raise ValueError('Invalid binary-XML chunk bounds')
        if kind == 1:
            count, _, flags, base, _ = struct.unpack_from('<IIIII', data, offset + 8)
            if header_size + count * 4 > chunk_size:
                raise ValueError('Invalid string-pool offsets')
            for index in range(count):
                relative = struct.unpack_from('<I', data, offset + header_size + index * 4)[0]
                position = offset + base + relative
                if flags & 0x100:
                    _, position = length_at(position, True)
                    length, position = length_at(position, True)
                    value = data[position:position + length].decode('utf-8')
                else:
                    length, position = length_at(position, False)
                    value = data[position:position + length * 2].decode('utf-16le')
                strings.append(value)
        elif kind == 0x102:
            _, name, start, stride, count, _, _, _ = struct.unpack_from('<IIHHHHHH', data, offset + 16)
            if stride < 20 or 16 + start + stride * count > chunk_size:
                raise ValueError('Invalid attribute bounds')
            element = strings[name]
            if element in ('manifest', 'uses-sdk', 'application'):
                attributes = {}
                for index in range(count):
                    position = offset + 16 + start + index * stride
                    _, attribute, raw, _, _, datatype, value = struct.unpack_from('<IIIHBBI', data, position)
                    attributes[strings[attribute]] = strings[raw] if raw != 0xffffffff else (strings[value] if datatype == 3 else value)
                elements.append({'element': element, 'attributes': attributes})
        offset += chunk_size
    return elements


def inspect(apk: Path) -> dict:
    with ZipFile(apk) as archive:
        names = archive.namelist()
        elements = manifest_elements(archive.read('AndroidManifest.xml'))
        attrs = {element['element']: element['attributes'] for element in elements}
        manifest = attrs.get('manifest', {})
        application = attrs.get('application', {})
        libraries = [name for name in names if name.startswith('lib/') and name.endswith('.so')]
        checks = {
            'zip_integrity': archive.testzip() is None,
            'isolated_review_package': manifest.get('package') == 'com.kaleb.havenline.review',
            'expected_version': manifest.get('versionCode') == 403 and manifest.get('versionName') == '0.4.3-outpost-review',
            'android_game_category': application.get('appCategory') == 0,
            'arm64_godot_runtime': 'lib/arm64-v8a/libgodot_android.so' in libraries,
            'no_other_architecture': bool(libraries) and all(name.startswith('lib/arm64-v8a/') for name in libraries),
            'no_unity_or_il2cpp_native_libraries': not any('unity' in name.lower() or 'il2cpp' in name.lower() for name in libraries),
            'npc_catalog_packaged': 'assets/data/npc-catalog.json' in names,
            'population_runtime_packaged': all(f'assets/scripts/{name}.gdc' in names for name in ('npc_population', 'population_simulation', 'population_view', 'render_policy')),
            'outpost_runtime_packaged': all(f'assets/scripts/{name}.gdc' in names for name in ('outpost_climate', 'outpost_simulation', 'outpost_view', 'outpost_audio', 'outpost_surface', 'action_readout')),
            'outpost_audio_remaps_packaged': all(f'assets/assets/audio/{name}.wav.remap' in names for name in ('wind', 'fire', 'wood', 'stone', 'transfer', 'upgrade')),
            'outpost_audio_imports_packaged': sum(n.startswith('assets/.godot/imported/') and n.endswith('.sample') and any('/' + clip + '.wav-' in n for clip in ('wind', 'fire', 'wood', 'stone', 'transfer', 'upgrade')) for n in names) == 6,
            'all_derived_crew_motion_packaged': all(f'assets/assets/motion/Character{i}.res' in names for i in (2, 3, 4)),
        }
    return {'apk': apk.name, 'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
            'manifest': elements, 'native_libraries': libraries, 'checks': checks,
            # Android deprecated isGame at API 26; appCategory=game is canonical.
            # https://developer.android.com/guide/topics/manifest/application-element#isGame
            'legacy_is_game': application.get('isGame'),
            'classification_basis': 'appCategory=game; deprecated isGame is informational only',
            'passed': all(checks.values()), 'signature_verification': 'Separate apksigner CI step',
            'physical_install_launch_verified': False, 'production_approved': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
