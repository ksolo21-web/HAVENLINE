"""Material-only R01 rebuild from immutable binary fixture; no model re-export.

Only enumerated body/enamel COLOR values, body triangle material membership,
and HL_blue roughness change. Geometry payloads are retained byte-for-byte.
"""
from __future__ import annotations
import base64, collections, copy, hashlib, json, struct
from pathlib import Path

BASE_SHA = '6d32499229dd22dde1ee32940bb1b0a506a0647ea911a4787b3bce83fe60a8e7'
BODY_TAGS = ('upper_rounded_pressure_shell', 'cap_transition', 'chimney_wall') + tuple('forged_lower_plate_%02d' % i for i in range(10) if i not in (7, 8))
FIXTURE = Path(__file__).with_name('fixtures') / 'hearth_material_source_v4.json'
FIXTURE_SHA = '17cdbc973ccb7744291c707f6c4d5e5f77c918b0f191e5bf74badc87c7484cf2'
FORGED_PBR = {'baseColorFactor': [.18, .22, .27, 1.], 'metallicFactor': .45, 'roughnessFactor': .55}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(raw):
    assert raw[:4] == b'glTF' and struct.unpack_from('<II', raw, 4) == (2, len(raw))
    length, kind = struct.unpack_from('<I4s', raw, 12)
    assert kind == b'JSON'
    doc = json.loads(raw[20:20 + length])
    size, kind = struct.unpack_from('<I4s', raw, 20 + length)
    assert kind == b'BIN\0'
    blob = raw[28 + length:28 + length + size]
    assert len(blob) == size and 28 + length + size == len(raw)
    return doc, blob


def payload(doc, blob, accessor):
    a = doc['accessors'][accessor]; v = doc['bufferViews'][a['bufferView']]
    assert 'byteStride' not in v and 'sparse' not in a
    components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a['type']]
    width = {5125: 4, 5126: 4}[a['componentType']]
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return blob[start:start + a['count'] * components * width]


def primitives_by_name(doc):
    return {doc['materials'][p['material']]['name']: p for p in doc['meshes'][0]['primitives']}


def triangles(doc, blob):
    out = collections.Counter()
    for p in doc['meshes'][0]['primitives']:
        data = payload(doc, blob, p['indices']); ids = struct.unpack('<%dI' % (len(data) // 4), data)
        # Accessor identity preserves oriented triangles even for duplicate positions.
        for i in range(0, len(ids), 3):
            out[(p['attributes']['POSITION'], *ids[i:i+3])] += 1
    return out


def encode(doc, blob):
    js = json.dumps(doc, sort_keys=True, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4); blob = bytes(blob) + b'\0' * (-len(blob) % 4)
    return struct.pack('<4sII', b'glTF', 2, 28 + len(js) + len(blob)) + struct.pack('<I4s', len(js), b'JSON') + js + struct.pack('<I4s', len(blob), b'BIN\0') + blob


def rebuild(path: Path | str) -> dict:
    fixture_bytes = FIXTURE.read_bytes()
    assert sha(fixture_bytes) == FIXTURE_SHA, 'Canonical material census drift'
    fixture = json.loads(fixture_bytes)
    assert fixture['baseline_glb_file'] == 'hearth_geometry_source_v4.glb'
    raw = FIXTURE.with_name(fixture['baseline_glb_file']).read_bytes()
    assert fixture['baseline_sha256'] == BASE_SHA == sha(raw), 'Immutable fixture drift'
    assert tuple(fixture['body_tags']) == BODY_TAGS
    assert fixture['blue_tag'] == 'enamel_armor_tab'
    before, baseline = unpack(raw); doc = copy.deepcopy(before); blob = bytearray(baseline)
    lookup = primitives_by_name(doc)
    assert len(before['materials']) == 9
    original_triangles = triangles(before, baseline)
    assert sum(original_triangles.values()) == 25968
    for name, expected in fixture['geometry_payload_sha256'].items():
        p = lookup[name]
        for semantic in ('POSITION', 'NORMAL'):
            assert sha(payload(doc, baseline, p['attributes'][semantic])) == expected[semantic]
    selections = set(); census = []; changed_colors = {}
    body_ranges = []
    for member in fixture['members']:
        kind = member['kind']; tag = member['tag']; material = member['baseline_material']
        assert (kind == 'body' and tag in BODY_TAGS and material == 'HL_cream') or (kind == 'blue' and tag == 'enamel_armor_tab' and material == 'HL_blue')
        start, count = member['vertex_start'], member['vertex_count']; p = lookup[material]
        positions = payload(doc, baseline, p['attributes']['POSITION'])[start*12:(start+count)*12]
        normals = payload(doc, baseline, p['attributes']['NORMAL'])[start*12:(start+count)*12]
        assert sha(positions) == member['position_sha256'] and sha(normals) == member['normal_sha256']
        assert sha(payload(doc, baseline, p['attributes']['COLOR_0'])[start*16:(start+count)*16]) == member['baseline_color_sha256']
        replacement = base64.b64decode(member['source_colors_with_v4_ao_base64'], validate=True)
        assert len(replacement) == count*16 and sha(replacement) == member['replacement_color_sha256']
        colors = changed_colors.setdefault(material, bytearray(payload(doc, baseline, p['attributes']['COLOR_0'])))
        colors[start*16:(start+count)*16] = replacement
        indices = set(range(start, start+count))
        if kind == 'body':
            assert not selections.intersection(indices); selections.update(indices); body_ranges.append(tag)
        census.append({'tag': tag, 'kind': kind, 'vertex_start': start, 'vertex_count': count, 'position_sha256': sha(positions), 'normal_sha256': sha(normals), 'replacement_color_sha256': sha(replacement)})
    assert collections.Counter(body_ranges) == collections.Counter(BODY_TAGS)
    assert len([m for m in census if m['kind'] == 'blue']) == fixture['blue_part_count'] == 8

    def append_accessor(data, typ, component, count, target):
        blob.extend(b'\0' * (-len(blob) % 4)); offset = len(blob); blob.extend(data)
        view = len(doc['bufferViews']); doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(data), 'target': target})
        index = len(doc['accessors']); doc['accessors'].append({'bufferView': view, 'componentType': component, 'count': count, 'type': typ})
        return index

    for material, colors in changed_colors.items():
        p = lookup[material]; p['attributes']['COLOR_0'] = append_accessor(colors, 'VEC4', 5126, len(colors)//16, 34962)
    cream = lookup['HL_cream']; index_data = payload(before, baseline, cream['indices'])
    ids = struct.unpack('<%dI' % (len(index_data)//4), index_data); retained=[]; body=[]
    for i in range(0, len(ids), 3):
        tri = ids[i:i+3]; membership = [index in selections for index in tri]
        assert all(membership) or not any(membership), 'Triangle crosses semantic membership'
        (body if all(membership) else retained).extend(tri)
    assert len(body)//3 == fixture['body_triangles'] and body and retained
    cream['indices'] = append_accessor(struct.pack('<%dI' % len(retained), *retained), 'SCALAR', 5125, len(retained), 34963)
    forged = copy.deepcopy(cream); forged['indices'] = append_accessor(struct.pack('<%dI' % len(body), *body), 'SCALAR', 5125, len(body), 34963)
    forged['material'] = len(doc['materials']); doc['materials'].append({'name':'HL_forged_iron','pbrMetallicRoughness':copy.deepcopy(FORGED_PBR),'doubleSided':False})
    doc['meshes'][0]['primitives'].append(forged)
    assert doc['materials'][cream['material']]['name'] == 'HL_cream'
    blue_index = lookup['HL_blue']['material']; doc['materials'][blue_index]['pbrMetallicRoughness']['roughnessFactor'] = .65
    doc['buffers'][0]['byteLength'] = len(blob)
    assert bytes(blob[:len(baseline)]) == baseline
    assert triangles(doc, blob) == original_triangles
    for i, material in enumerate(before['materials']):
        expected = copy.deepcopy(material)
        if material['name'] == 'HL_blue': expected['pbrMetallicRoughness']['roughnessFactor'] = .65
        assert doc['materials'][i] == expected
    result = encode(doc, blob); output = Path(path); output.parent.mkdir(parents=True, exist_ok=True); output.write_bytes(result)
    return {'source_fixture_sha256':BASE_SHA,'sha256':sha(result),'triangles':25968,'materials':[m['name'][3:] for m in doc['materials']], 'proof':{'geometry_payload_bytes_unchanged':True,'oriented_index_multiset_unchanged':True,'baseline_binary_prefix_unchanged':True,'body_tags':list(BODY_TAGS),'body_triangles':len(body)//3,'blue_tag':'enamel_armor_tab','blue_parts':8,'actual_hearth_material_count':len(doc['materials']),'kit_material_vocabulary_count_expected':12,'original_material_definitions_preserved_except_blue_roughness':True,'members':census}}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    args = parser.parse_args(); print(json.dumps(rebuild(args.output), indent=2))
