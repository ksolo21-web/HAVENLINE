#!/usr/bin/env python3
"""Build four original T10 resource pictograms; no external font/art dependency.

Requires fontTools only to regenerate. The game consumes the committed native Godot FontFile resource.
Private-use glyphs always accompany written resource names and authoritative counts.
"""
from pathlib import Path
from io import BytesIO
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'HavenlineGodot/assets/world_transform_v1/resource_symbols.tres'


def polygon(pen, points):
    pen.moveTo(points[0])
    for point in points[1:]:
        pen.lineTo(point)
    pen.closePath()


def ellipse(pen, x, y, rx, ry, reverse=False):
    # Quadratic contours; opposite winding makes the cut end's annual ring hollow.
    if reverse:
        pen.moveTo((x + rx, y));pen.qCurveTo((x + rx, y - ry), (x, y - ry));pen.qCurveTo((x - rx, y - ry), (x - rx, y));pen.qCurveTo((x - rx, y + ry), (x, y + ry));pen.qCurveTo((x + rx, y + ry), (x + rx, y))
    else:
        pen.moveTo((x + rx, y));pen.qCurveTo((x + rx, y + ry), (x, y + ry));pen.qCurveTo((x - rx, y + ry), (x - rx, y));pen.qCurveTo((x - rx, y - ry), (x, y - ry));pen.qCurveTo((x + rx, y - ry), (x + rx, y))
    pen.closePath()


def build():
    names = ['.notdef', 'wood', 'stone', 'metal', 'fuel']
    glyphs = {}
    for name in names:
        pen = TTGlyphPen(None)
        if name == 'wood':
            # A horizontal cut log: elongated bark body and two nested end rings.
            polygon(pen, [(280, 160), (730, 260), (820, 410), (780, 650), (640, 730), (220, 650)])
            ellipse(pen, 245, 405, 180, 260)
            ellipse(pen, 245, 405, 115, 190, reverse=True)
            ellipse(pen, 245, 405, 48, 105)
            polygon(pen, [(400, 380), (735, 455), (735, 490), (400, 415)][::-1])
            polygon(pen, [(400, 540), (700, 607), (710, 647), (400, 580)][::-1])
        elif name == 'stone':
            polygon(pen, [(95, 240), (220, 650), (470, 780), (735, 630), (850, 300), (620, 120), (290, 120)])
            polygon(pen, [(220, 310), (335, 575), (610, 540), (460, 355)][::-1])
        elif name == 'metal':
            polygon(pen, [(75, 200), (265, 640), (700, 640), (880, 200)])
            polygon(pen, [(295, 550), (650, 550), (700, 435), (245, 435)][::-1])
            polygon(pen, [(185, 290), (755, 290), (720, 350), (210, 350)][::-1])
        elif name == 'fuel':
            pen.moveTo((480, 840));pen.qCurveTo((400, 690), (230, 500));pen.qCurveTo((60, 310), (190, 155));pen.qCurveTo((460, -10), (705, 160));pen.qCurveTo((825, 340), (625, 575));pen.qCurveTo((520, 715), (480, 840));pen.closePath()
            ellipse(pen, 400, 275, 75, 100, reverse=True)
        glyphs[name] = pen.glyph()
    font = FontBuilder(1000, isTTF=True)
    font.setupGlyphOrder(names)
    font.setupCharacterMap({0xE000+i: name for i, name in enumerate(names[1:])})
    font.setupGlyf(glyphs)
    font.setupHorizontalMetrics({name: (950, 0) for name in names})
    font.setupHorizontalHeader(ascent=850, descent=-150)
    font.setupNameTable({'familyName': 'Havenline T10 Resource Symbols', 'styleName': 'Regular',
        'uniqueFontIdentifier': 'Havenline-T10-Resource-Symbols-1', 'fullName': 'Havenline T10 Resource Symbols',
        'psName': 'HavenlineT10ResourceSymbols', 'version': 'Version 1.000',
        'copyright': 'Original neutral resource vectors authored for the Havenline project.'})
    font.setupOS2(sTypoAscender=850, sTypoDescender=-150, usWinAscent=850, usWinDescent=150, fsType=0)
    font.setupPost()
    font.setupMaxp()
    font.font['head'].created = font.font['head'].modified = 2082844800
    font.font.recalcTimestamp = False
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    binary = BytesIO()
    font.save(binary)
    values = ', '.join(str(value) for value in binary.getvalue())
    OUTPUT.write_text('[gd_resource type="FontFile" format=3]\n\n[resource]\ndata = PackedByteArray(' + values + ')\n')
    print(OUTPUT)


if __name__ == '__main__':
    build()
