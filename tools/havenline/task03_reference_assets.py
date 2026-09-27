#!/usr/bin/env python3
"""Canonical decimal encoding for exact-source T03 OBJ byte verification.

Revision 18 binds the canonical export to the latest user-supplied chunky
early-camp palisade/gate silhouette while preserving all 11H gameplay authority.

Preserve the raw author's topology/material records and bound every changed numeric
component to 0.000001 model units. This is encoding, not an art/authority change.
The original raw generator still performs every model, authority and hash check.
"""
from __future__ import annotations
import math,json,sys
from pathlib import Path
import task03_reference_assets_raw as authoring
_original_export=authoring.export_obj
_AUTHORIZED_GEOMETRY_WRITE='--write' in sys.argv


def canonicalize(raw: str) -> str:
    lines=[]
    for line in raw.splitlines():
        fields=line.split()
        if fields and fields[0] in ('v','vt','vn'):
            values=[]
            for token in fields[1:]:
                x=float(token)
                if not math.isfinite(x):raise ValueError('Nonfinite OBJ component')
                encoded=f'{x:.6f}'
                if encoded=='-0.000000':encoded='0.000000'
                if abs(float(encoded)-x)>0.000000500001:raise ValueError('OBJ encoding precision exceeded')
                values.append(encoded)
            line=fields[0]+' '+' '.join(values)
        lines.append(line)
    return '\n'.join(lines)+'\n'


def equivalent_encoding(before,after):
    a=before.splitlines();b=after.splitlines()
    if len(a)!=len(b):raise ValueError('Encoding repair changed OBJ record count')
    maximum=0.;changed=0
    for x,y in zip(a,b):
        if x==y:continue
        xx=x.split();yy=y.split()
        if not xx or xx[0] not in ('v','vt','vn') or len(xx)!=len(yy) or xx[0]!=yy[0]:
            raise ValueError('Encoding repair changed OBJ topology or material assignment')
        error=max(abs(float(p)-float(q)) for p,q in zip(xx[1:],yy[1:]))
        if not math.isfinite(error) or error>0.000001:raise ValueError('Encoding repair changed modeled geometry')
        maximum=max(maximum,error);changed+=1
    return {'numeric_records_changed':changed,'max_component_difference':maximum,'non_numeric_records_unchanged':True}


def export_obj(model,path):
    _original_export(model,path)
    raw=Path(path).read_text();encoded=canonicalize(raw)
    assert canonicalize(encoded)==encoded,'OBJ encoding not idempotent'
    equivalent_encoding(raw,encoded)
    committed=authoring.OUT/(model.name+'.obj')
    if committed.exists() and not _AUTHORIZED_GEOMETRY_WRITE:
        diagnostic=equivalent_encoding(committed.read_text(),encoded)
        print(json.dumps({'encoding_comparison':model.name,**diagnostic}),file=sys.stderr)
    Path(path).write_text(encoded)


def self_test():
    sample='v -0.00000000000003 1.20000000000001 0.99999999999999\nvn 0 -1 0\nvt .25 .5\nf 1/1/1 2/2/2 3/3/3\n'
    out=canonicalize(sample)
    assert out.startswith('v 0.000000 1.200000 1.000000\n') and canonicalize(out)==out
    equivalent_encoding(sample,out)
    for value in ('nan','inf','-inf'):
        try:canonicalize('v '+value+' 0 0\n')
        except ValueError:pass
        else:raise AssertionError('Nonfinite value accepted')
    for bad in (out.replace('1.200000','1.300000'),out.replace('f 1/1/1','f 2/1/1'),out+'s 1\n'):
        try:equivalent_encoding(out,bad)
        except ValueError:pass
        else:raise AssertionError('Geometry/topology change accepted as encoding')


if __name__=='__main__':
    self_test();authoring.export_obj=export_obj;authoring.main()
