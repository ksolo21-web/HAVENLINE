"""Inspect the exported APK itself; source configuration is not export evidence.

Signature verification is performed separately by Android SDK apksigner in CI.
This parser only reads the binary manifest and checks packaging invariants.
"""
from __future__ import annotations

import argparse
import configparser
import io
import hashlib
import json
import struct
from pathlib import Path, PurePosixPath
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


def audio_import_targets(archive: ZipFile) -> dict[str, str]:
    """Resolve exported WAV import records to real, nonempty sample resources.

    Imported WAVs retain .wav.import metadata, not .wav.remap metadata.
    A matching filename alone does not prove the audio resource is usable.
    """
    names = archive.namelist()
    targets: dict[str, str] = {}
    for clip in ('wind', 'fire', 'wood', 'stone', 'transfer', 'upgrade'):
        record = f'assets/assets/audio/{clip}.wav.import'
        if names.count(record) != 1:
            continue
        try:
            # The actual Android APK contains NUL-terminated .import text.
            # Strip terminators only; an embedded NUL remains an invalid record.
            text = archive.read(record).decode('utf-8').rstrip('\x00')
            if '\x00' in text:
                continue
            config = configparser.ConfigParser(interpolation=None, strict=True,
                                               inline_comment_prefixes=(';',))
            config.read_string(text)
            # Android exports strip the editor-only type field; validate it when present.
            if config.has_option('remap', 'type') and json.loads(config.get('remap', 'type')) != 'AudioStreamWAV':
                continue
            resource = json.loads(config.get('remap', 'path'))
            if not isinstance(resource, str) or not resource.startswith('res://.godot/imported/'):
                continue
            relative = resource.removeprefix('res://')
            if '..' in PurePosixPath(relative).parts or '\\' in relative:
                continue
            target = 'assets/' + relative
            if not PurePosixPath(target).name.startswith(clip + '.wav-') or not target.endswith('.sample'):
                continue
            if names.count(target) != 1 or archive.getinfo(target).file_size < 16:
                continue
            with archive.open(target) as stream:
                if stream.read(4) not in (b'RSRC', b'RSCC'):
                    continue
            targets[clip] = target
        except (KeyError, ValueError, TypeError, configparser.Error, UnicodeError):
            continue
    return targets


def self_test() -> dict:
    """Exercise valid, absent, stale, malformed and unsafe audio import records."""
    def fixture(record: str | None, payload: bytes | None = b'RSRC' + b'\0' * 28,
                target: str = 'assets/.godot/imported/wind.wav-test.sample') -> dict:
        output = io.BytesIO()
        with ZipFile(output, 'w') as archive:
            if record is not None:
                archive.writestr('assets/assets/audio/wind.wav.import', record)
            if payload is not None:
                archive.writestr(target, payload)
        with ZipFile(io.BytesIO(output.getvalue())) as archive:
            return audio_import_targets(archive)
    valid = '[remap]\ntype="AudioStreamWAV"\npath="res://.godot/imported/wind.wav-test.sample"\n'
    tests = {
        'valid_import_resolves': 'wind' in fixture(valid),
        'stripped_export_import_resolves': 'wind' in fixture(valid.replace('type="AudioStreamWAV"\n', '')),
        'nul_terminated_export_resolves': 'wind' in fixture(valid + '\x00'),
        'multiple_terminators_resolve': 'wind' in fixture(valid + '\x00\x00'),
        'stripped_nul_terminated_export_resolves': 'wind' in fixture(valid.replace('type="AudioStreamWAV"\n', '') + '\x00'),
        'embedded_nul_rejected': not fixture(valid.replace('wind.wav', 'wind\x00.wav')),
        'commented_scalar_resolves': 'wind' in fixture(valid.replace('.sample"', '.sample" ; imported audio')),
        'noncomment_trailing_junk_rejected': not fixture(valid.replace('.sample"', '.sample" garbage')),
        'duplicate_path_rejected': not fixture(valid + 'path="res://.godot/imported/wind.wav-test.sample"\n'),
        'missing_record_rejected': not fixture(None),
        'missing_sample_rejected': not fixture(valid, None),
        'empty_sample_rejected': not fixture(valid, b''),
        'wrong_resource_magic_rejected': not fixture(valid, b'fake' + b'\0' * 28),
        'compressed_sample_accepted': 'wind' in fixture(valid, b'RSCC' + b'\0' * 28),
        'wrong_resource_type_rejected': not fixture(valid.replace('AudioStreamWAV', 'Texture2D')),
        'foreign_resource_path_rejected': not fixture(valid.replace('res://', 'user://')),
        'traversal_rejected': not fixture(valid.replace('imported/', 'imported/../')),
        'wrong_clip_rejected': not fixture(valid.replace('wind.wav-', 'fire.wav-')),
        'malformed_record_rejected': not fixture('[remap]\npath=invalid\n'),
        'wrong_sample_extension_rejected': not fixture(valid.replace('.sample', '.png')),
    }
    return {'checks': tests, 'total_checks': len(tests), 'passed': all(tests.values())}


def inspect(apk: Path) -> dict:
    with ZipFile(apk) as archive:
        names = archive.namelist()
        elements = manifest_elements(archive.read('AndroidManifest.xml'))
        attrs = {element['element']: element['attributes'] for element in elements}
        manifest = attrs.get('manifest', {})
        application = attrs.get('application', {})
        libraries = [name for name in names if name.startswith('lib/') and name.endswith('.so')]
        audio_targets = audio_import_targets(archive)
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
            'outpost_audio_import_references_resolve': len(audio_targets) == 6,
            'outpost_audio_imports_packaged': sum(n.startswith('assets/.godot/imported/') and n.endswith('.sample') and any('/' + clip + '.wav-' in n for clip in ('wind', 'fire', 'wood', 'stone', 'transfer', 'upgrade')) for n in names) == 6,
            'all_derived_crew_motion_packaged': all(f'assets/assets/motion/Character{i}.res' in names for i in (2, 3, 4)),
        }
    return {'apk': apk.name, 'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
            'manifest': elements, 'native_libraries': libraries, 'checks': checks,
            'audio_import_targets': audio_targets,
            # Android deprecated isGame at API 26; appCategory=game is canonical.
            # https://developer.android.com/guide/topics/manifest/application-element#isGame
            'legacy_is_game': application.get('isGame'),
            'classification_basis': 'appCategory=game; deprecated isGame is informational only',
            'passed': all(checks.values()), 'signature_verification': 'Separate apksigner CI step',
            'physical_install_launch_verified': False, 'production_approved': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path, nargs='?')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.self_test and args.apk is None:
        parser.error('APK path is required unless --self-test is specified')
    preflight = self_test()
    result = preflight if args.self_test else inspect(args.apk)
    if not args.self_test:
        result['verifier_self_test'] = preflight
        result['passed'] = result['passed'] and preflight['passed']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
