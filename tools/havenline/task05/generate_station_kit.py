#!/usr/bin/env python3
"""Generate Havenline's deterministic authored T05 station/prop GLBs.

The generator uses explicit sculpted/chamfered geometry and named production
materials. It does not use engine debug primitives, downloaded assets or
third-party geometry. Re-running it must reproduce byte-identical assets.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "HavenlineGodot" / "assets" / "stations_v2"
TAU = math.tau

MATERIALS = {
    "snow": ((0.86, 0.94, 1.0, 1.0), 0.0, 0.82),
    "cream": ((0.96, 0.84, 0.63, 1.0), 0.0, 0.72),
    "wood": ((0.44, 0.20, 0.105, 1.0), 0.0, 0.78),
    "wood_light": ((0.68, 0.37, 0.17, 1.0), 0.0, 0.72),
    "metal": ((0.15, 0.23, 0.30, 1.0), 0.72, 0.30),
    "blue": ((0.075, 0.32, 0.60, 1.0), 0.18, 0.40),
    "cyan": ((0.10, 0.68, 0.82, 1.0), 0.12, 0.34),
    "orange": ((0.96, 0.34, 0.08, 1.0), 0.08, 0.38),
    "yellow": ((1.0, 0.68, 0.08, 1.0), 0.05, 0.42),
    "green": ((0.12, 0.64, 0.29, 1.0), 0.05, 0.48),
    "red": ((0.78, 0.12, 0.10, 1.0), 0.05, 0.50),
    "dark": ((0.035, 0.07, 0.11, 1.0), 0.18, 0.42),
}


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(max(0.0, a[0] * a[0] + a[1] * a[1] + a[2] * a[2]))


def vnorm(a):
    length = vlen(a)
    return (0.0, 1.0, 0.0) if length < 1e-10 else vmul(a, 1.0 / length)


def rotation_matrix(rx=0.0, ry=0.0, rz=0.0):
    sx, cx = math.sin(rx), math.cos(rx)
    sy, cy = math.sin(ry), math.cos(ry)
    sz, cz = math.sin(rz), math.cos(rz)
    return (
        (cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz),
        (cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz),
        (-sy, sx * cy, cx * cy),
    )


def mat_vec(m, v):
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


@dataclass
class Surface:
    positions: list[tuple[float, float, float]] = field(default_factory=list)
    normals: list[tuple[float, float, float]] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)


class MeshBuilder:
    def __init__(self, name: str):
        self.name = name
        self.surfaces: dict[str, Surface] = {}

    def _surface(self, material: str) -> Surface:
        if material not in MATERIALS:
            raise ValueError(f"unknown material {material}")
        return self.surfaces.setdefault(material, Surface())

    def triangles(self, material, vertices, normals, indices, center=(0, 0, 0), rotation=(0, 0, 0)):
        surface = self._surface(material)
        base = len(surface.positions)
        matrix = rotation_matrix(*rotation)
        surface.positions.extend(vadd(mat_vec(matrix, p), center) for p in vertices)
        surface.normals.extend(vnorm(mat_vec(matrix, n)) for n in normals)
        # Primitive helpers describe both smooth normals and topology. Guarantee
        # their winding agrees so Godot's normal back-face culling cannot make a
        # valid vessel, counter, or fixture vanish from one evidence shoulder.
        oriented = list(indices)
        for triangle in range(0, len(oriented), 3):
            ia, ib, ic = oriented[triangle:triangle + 3]
            geometric = vcross(vsub(vertices[ib], vertices[ia]), vsub(vertices[ic], vertices[ia]))
            authored = vnorm(vadd(vadd(normals[ia], normals[ib]), normals[ic]))
            if sum(geometric[i] * authored[i] for i in range(3)) < 0.0:
                oriented[triangle + 1], oriented[triangle + 2] = ic, ib
        surface.indices.extend(base + i for i in oriented)

    def beveled_box(self, material, center, size, bevel=0.08, rotation=(0, 0, 0)):
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        bevel = max(0.001, min(bevel, hx * 0.46, hy * 0.46, hz * 0.46))
        half = (hx, hy, hz)
        inner = (hx - bevel, hy - bevel, hz - bevel)
        verts, norms, inds = [], [], []
        axes = [
            (0, 1, 2, 1), (0, 1, 2, -1),
            (1, 0, 2, 1), (1, 0, 2, -1),
            (2, 0, 1, 1), (2, 0, 1, -1),
        ]
        for fixed, ua, va, sign in axes:
            us = [-half[ua], -inner[ua], inner[ua], half[ua]]
            vs = [-half[va], -inner[va], inner[va], half[va]]
            grid = []
            for vv in vs:
                row = []
                for uu in us:
                    p = [0.0, 0.0, 0.0]
                    p[fixed] = sign * half[fixed]
                    p[ua], p[va] = uu, vv
                    q = [max(-inner[i], min(inner[i], p[i])) for i in range(3)]
                    delta = vsub(tuple(p), tuple(q))
                    n = vnorm(delta)
                    pos = vadd(tuple(q), vmul(n, bevel))
                    row.append(len(verts)); verts.append(pos); norms.append(n)
                grid.append(row)
            for y in range(3):
                for x in range(3):
                    a, b, c, d = grid[y][x], grid[y][x + 1], grid[y + 1][x + 1], grid[y + 1][x]
                    if sign > 0:
                        inds.extend((a, c, b, a, d, c))
                    else:
                        inds.extend((a, b, c, a, c, d))
        self.triangles(material, verts, norms, inds, center, rotation)

    def cylinder(self, material, center, radius, height, segments=16, rotation=(0, 0, 0), top_radius=None):
        top_radius = radius if top_radius is None else top_radius
        verts, norms, inds = [], [], []
        slope = (radius - top_radius) / max(height, 1e-6)
        for y, rad in [(-height / 2, radius), (height / 2, top_radius)]:
            for i in range(segments):
                angle = TAU * i / segments
                verts.append((math.cos(angle) * rad, y, math.sin(angle) * rad))
                norms.append(vnorm((math.cos(angle), slope, math.sin(angle))))
        for i in range(segments):
            j = (i + 1) % segments
            inds.extend((i, segments + j, j, i, segments + i, segments + j))
        bottom = len(verts); verts.append((0, -height / 2, 0)); norms.append((0, -1, 0))
        top = len(verts); verts.append((0, height / 2, 0)); norms.append((0, 1, 0))
        for i in range(segments):
            j = (i + 1) % segments
            inds.extend((bottom, j, i, top, segments + i, segments + j))
        self.triangles(material, verts, norms, inds, center, rotation)

    def sphere(self, material, center, radii, rings=8, segments=16, rotation=(0, 0, 0)):
        verts, norms, inds = [], [], []
        for r in range(rings + 1):
            phi = math.pi * r / rings
            sy, sr = math.cos(phi), math.sin(phi)
            for i in range(segments):
                angle = TAU * i / segments
                unit = (math.cos(angle) * sr, sy, math.sin(angle) * sr)
                verts.append((unit[0] * radii[0], unit[1] * radii[1], unit[2] * radii[2]))
                norms.append(vnorm((unit[0] / radii[0], unit[1] / radii[1], unit[2] / radii[2])))
        for r in range(rings):
            for i in range(segments):
                j = (i + 1) % segments
                a, b = r * segments + i, r * segments + j
                c, d = (r + 1) * segments + j, (r + 1) * segments + i
                inds.extend((a, c, b, a, d, c))
        self.triangles(material, verts, norms, inds, center, rotation)

    def lathe(self, material, center, profile, segments=20, rotation=(0, 0, 0)):
        verts, norms, inds = [], [], []
        for ring, (radius, y) in enumerate(profile):
            prev = profile[max(0, ring - 1)]
            nxt = profile[min(len(profile) - 1, ring + 1)]
            tangent = (nxt[0] - prev[0], nxt[1] - prev[1])
            for i in range(segments):
                angle = TAU * i / segments
                radial = (math.cos(angle), 0.0, math.sin(angle))
                normal = vnorm((radial[0] * tangent[1], -tangent[0], radial[2] * tangent[1]))
                verts.append((radial[0] * radius, y, radial[2] * radius)); norms.append(normal)
        for ring in range(len(profile) - 1):
            for i in range(segments):
                j = (i + 1) % segments
                a, b = ring * segments + i, ring * segments + j
                c, d = (ring + 1) * segments + j, (ring + 1) * segments + i
                inds.extend((a, c, b, a, d, c))
        self.triangles(material, verts, norms, inds, center, rotation)

    def torus(self, material, center, major, minor, segments=20, sides=8, rotation=(0, 0, 0), arc=TAU):
        verts, norms, inds = [], [], []
        ring_count = segments + 1 if arc < TAU - 1e-5 else segments
        for i in range(ring_count):
            u = arc * i / segments
            for j in range(sides):
                v = TAU * j / sides
                normal = (math.cos(u) * math.cos(v), math.sin(v), math.sin(u) * math.cos(v))
                verts.append((math.cos(u) * (major + minor * math.cos(v)), minor * math.sin(v), math.sin(u) * (major + minor * math.cos(v))))
                norms.append(normal)
        loops = segments if arc < TAU - 1e-5 else segments
        for i in range(loops):
            ni = i + 1 if arc < TAU - 1e-5 else (i + 1) % segments
            for j in range(sides):
                nj = (j + 1) % sides
                a, b, c, d = i * sides + j, i * sides + nj, ni * sides + nj, ni * sides + j
                inds.extend((a, c, b, a, d, c))
        self.triangles(material, verts, norms, inds, center, rotation)

    def rod_between(self, material, a, b, radius=0.045, segments=10):
        delta = vsub(b, a); length = vlen(delta)
        if length < 1e-6:
            return
        direction = vnorm(delta)
        yaw = math.atan2(direction[0], direction[2])
        pitch = math.acos(max(-1.0, min(1.0, direction[1])))
        self.cylinder(material, vmul(vadd(a, b), 0.5), radius, length, segments, rotation=(pitch, yaw, 0))

    def triangle_count(self):
        return sum(len(s.indices) // 3 for s in self.surfaces.values())


def add_snow_foot(builder, size=(2.0, 0.12, 2.0), center=(0, 0.02, 0)):
    builder.beveled_box("snow", center, size, min(size) * 0.18)


def build_hearth():
    b = MeshBuilder("hearth_vessel")
    add_snow_foot(b, (2.6, .16, 2.25))
    b.cylinder("wood", (0, .18, 0), 1.02, .26, 20)
    b.cylinder("blue", (0, .35, 0), .88, .20, 20)
    b.lathe("metal", (0, .48, 0), [(.72, 0), (.82, .18), (.76, .62), (.60, .83), (.53, .90)], 24)
    b.lathe("orange", (0, .55, 0), [(.50, 0), (.56, .11), (.48, .34), (.37, .44)], 24)
    b.torus("yellow", (0, 1.36, 0), .60, .075, 24, 8)
    b.cylinder("cream", (0, 1.48, 0), .48, .16, 20, top_radius=.42)
    for x in (-.72, .72):
        b.beveled_box("blue", (x, .72, .1), (.20, .92, .30), .07, rotation=(0, 0, .12 if x < 0 else -.12))
        b.cylinder("yellow", (x, 1.18, .1), .14, .18, 12)
    b.cylinder("metal", (0, 1.76, .38), .18, .78, 14)
    b.torus("orange", (0, 2.08, .35), .27, .09, 12, 8, rotation=(math.pi / 2, 0, 0), arc=math.pi)
    b.beveled_box("wood_light", (0, .55, -.76), (.76, .38, .20), .08)
    return b


def add_counter_frame(b, process=False):
    add_snow_foot(b, (3.45, .14, 1.95))
    b.beveled_box("wood", (0, .55, 0), (3.05, .95, 1.46), .16)
    b.beveled_box("wood_light", (0, 1.10, -.02), (3.34, .22, 1.70), .09)
    b.beveled_box("blue", (0, .70, -.745), (2.46, .56, .12), .04)
    for x in (-1.28, 1.28):
        b.beveled_box("metal", (x, .48, 0), (.18, .78, 1.30), .055)
    for x in (-.74, 0, .74):
        b.beveled_box("yellow" if process else "cyan", (x, .72, -.82), (.46, .18, .10), .04)
    b.beveled_box("dark", (0, .42, .44), (2.25, .08, .48), .025)


def build_service_counter():
    b = MeshBuilder("service_counter"); add_counter_frame(b)
    for x in (-.80, 0, .80):
        b.cylinder("green", (x, 1.30, 0), .16, .12, 12)
        b.cylinder("cream", (x, 1.39, 0), .12, .08, 12)
    b.beveled_box("orange", (0, 1.24, .55), (.78, .12, .28), .04)
    return b


def build_process_counter():
    b = MeshBuilder("processing_counter"); add_counter_frame(b, True)
    for x in (-.72, .72):
        b.cylinder("metal", (x, 1.45, .02), .34, .54, 18)
        b.torus("orange", (x, 1.73, .02), .27, .06, 18, 8)
        b.cylinder("cyan", (x, 1.77, .02), .12, .10, 12)
    b.beveled_box("blue", (0, 1.34, .44), (.54, .58, .30), .07)
    b.cylinder("yellow", (0, 1.66, .44), .11, .12, 12)
    return b


def add_arrow(b, material, center, direction=1.0, pair=False):
    offsets = (-.34, .34) if pair else (0,)
    for x in offsets:
        z0 = center[2] - .25 * direction
        z1 = center[2] + .25 * direction
        b.rod_between(material, (center[0] + x, center[1], z0), (center[0] + x, center[1], z1), .065, 8)
        b.rod_between(material, (center[0] + x, center[1], z1), (center[0] + x - .16, center[1], z1 - .16 * direction), .065, 8)
        b.rod_between(material, (center[0] + x, center[1], z1), (center[0] + x + .16, center[1], z1 - .16 * direction), .065, 8)


def build_pad(kind, material):
    b = MeshBuilder("pad_" + kind)
    b.cylinder("wood", (0, .07, 0), 1.02, .14, 12)
    b.cylinder(material, (0, .16, 0), .92, .12, 12)
    b.cylinder("cream", (0, .235, 0), .70, .05, 12)
    y = .30
    if kind == "build":
        for x in (-.23, .23): b.beveled_box(material, (x, y, 0), (.25, .10, .58), .035)
        b.beveled_box(material, (0, y, 0), (.70, .10, .18), .035)
    elif kind == "upgrade":
        b.rod_between(material, (-.42, y, .18), (0, y, -.25), .075, 8)
        b.rod_between(material, (0, y, -.25), (.42, y, .18), .075, 8)
        b.rod_between(material, (0, y, .34), (0, y, -.20), .075, 8)
    elif kind == "input": add_arrow(b, material, (0, y, 0), 1.0, True)
    elif kind == "output": add_arrow(b, material, (0, y, 0), -1.0, True)
    elif kind == "stock":
        for z in (-.20, .20): b.beveled_box(material, (0, y, z), (.82, .10, .22), .04)
        for x in (-.31, .31): b.beveled_box(material, (x, y, 0), (.20, .10, .62), .04)
    else:
        for x, z, s in [(-.27, -.16, .26), (.02, .12, .30), (.30, -.10, .22)]:
            b.cylinder(material, (x, y + s * .14, z), s, s * .20, 16)
            b.cylinder("cream", (x, y + s * .25, z), s * .55, s * .06, 12)
    return b


def build_fishing_rack():
    b = MeshBuilder("fishing_rack"); add_snow_foot(b, (3.25, .12, 1.45))
    for x in (-1.30, 1.30):
        b.beveled_box("wood", (x, .68, 0), (.20, 1.30, .30), .07)
        b.cylinder("blue", (x, 1.36, 0), .15, .16, 12)
    b.beveled_box("wood_light", (0, .55, 0), (2.65, .18, .26), .06)
    b.beveled_box("blue", (0, .98, 0), (2.72, .16, .22), .05)
    for i, x in enumerate((-.96, -.32, .32, .96)):
        b.rod_between("yellow", (x, .96, 0), (x + .34, 2.55, -.35 - .08 * i), .045, 10)
        b.cylinder("orange", (x, .91, -.04), .12, .12, 12, rotation=(math.pi / 2, 0, 0))
    b.lathe("wood_light", (0, .20, .46), [(.52, 0), (.60, .20), (.52, .44), (.40, .50)], 16)
    b.torus("cyan", (0, .70, .46), .42, .045, 16, 6)
    return b


def build_intake():
    b = MeshBuilder("intake_machine"); add_snow_foot(b, (2.6, .14, 2.4))
    b.beveled_box("blue", (0, .54, 0), (2.18, .90, 1.72), .18)
    b.beveled_box("metal", (0, 1.10, 0), (1.82, .28, 1.32), .10)
    b.lathe("orange", (0, 1.20, -.12), [(.80, 0), (.70, .20), (.46, .78), (.32, .90)], 20)
    for x in (-.68, .68):
        b.cylinder("yellow", (x, .78, .83), .18, .30, 14, rotation=(math.pi / 2, 0, 0))
        b.cylinder("dark", (x, .78, .88), .09, .34, 12, rotation=(math.pi / 2, 0, 0))
    b.beveled_box("cyan", (0, .66, -.90), (1.18, .22, .32), .07)
    return b


def build_cooker():
    b = MeshBuilder("cooker_processor"); add_snow_foot(b, (2.45, .14, 2.15))
    b.beveled_box("blue", (0, .65, 0), (1.94, 1.15, 1.54), .22)
    b.beveled_box("metal", (0, .72, -.79), (1.28, .66, .12), .045)
    b.beveled_box("orange", (0, .72, -.86), (.96, .42, .08), .035)
    b.torus("yellow", (0, 1.30, 0), .60, .07, 20, 8)
    b.cylinder("cream", (0, 1.34, 0), .54, .12, 20)
    b.cylinder("metal", (.55, 1.82, .32), .14, 1.05, 14)
    b.torus("orange", (.55, 2.28, .32), .22, .07, 12, 8, rotation=(math.pi / 2, 0, 0), arc=math.pi)
    b.beveled_box("wood_light", (0, .54, .92), (1.46, .18, .56), .07)
    return b


def build_conveyor():
    b = MeshBuilder("conveyor_straight"); add_snow_foot(b, (3.35, .10, 1.30))
    for x in (-1.46, 1.46):
        for z in (-.46, .46): b.beveled_box("blue", (x, .42, z), (.16, .74, .16), .05)
    b.beveled_box("blue", (0, .66, -.50), (3.08, .18, .16), .05)
    b.beveled_box("blue", (0, .66, .50), (3.08, .18, .16), .05)
    b.beveled_box("dark", (0, .73, 0), (2.94, .12, .82), .05)
    for x in (-1.30, -.65, 0, .65, 1.30):
        b.cylinder("yellow", (x, .77, 0), .10, .92, 12, rotation=(math.pi / 2, 0, math.pi / 2))
    for x in (-1.5, 1.5): b.cylinder("orange", (x, .74, 0), .20, 1.05, 14, rotation=(math.pi / 2, 0, 0))
    return b


def build_defense():
    b = MeshBuilder("defense_platform"); add_snow_foot(b, (3.25, .16, 3.05))
    b.cylinder("wood", (0, .28, 0), 1.38, .38, 12)
    b.cylinder("blue", (0, .52, 0), 1.12, .18, 12)
    for a in range(8):
        angle = TAU * a / 8
        x, z = math.cos(angle) * 1.06, math.sin(angle) * 1.06
        b.beveled_box("wood_light", (x, .82, z), (.20, .78, .28), .06, rotation=(0, -angle, 0))
    b.cylinder("metal", (0, 1.00, 0), .46, .80, 18)
    b.torus("orange", (0, 1.42, 0), .44, .10, 20, 8)
    b.cylinder("dark", (0, 1.48, 0), .26, .16, 16)
    b.beveled_box("yellow", (0, .82, -.78), (.62, .18, .28), .06)
    return b


def build_wood_stack():
    b = MeshBuilder("wood_stack"); add_snow_foot(b, (1.70, .10, 1.18))
    for row, y in enumerate((.24, .50, .76)):
        count = 4 - row
        for i in range(count):
            x = (i - (count - 1) / 2) * .38
            b.cylinder("wood_light", (x, y, 0), .15, .88, 12, rotation=(math.pi / 2, 0, 0))
            for z in (-.45, .45): b.cylinder("cream", (x, y, z), .12, .035, 12, rotation=(math.pi / 2, 0, 0))
    return b


def build_stone_stack():
    b = MeshBuilder("stone_stack"); add_snow_foot(b, (1.65, .10, 1.38))
    stones = [(-.48,.25,-.22,.42),(.0,.23,.18,.46),(.48,.24,-.12,.40),(-.25,.61,.16,.36),(.28,.60,-.14,.38),(0,.91,.02,.30)]
    for x,y,z,s in stones: b.sphere("metal", (x,y,z), (s,s*.68,s*.82), 7, 12, rotation=(0,x*.5,z*.4))
    return b


def build_metal_stack():
    b = MeshBuilder("metal_stack"); add_snow_foot(b, (1.75, .10, 1.25))
    for row in range(3):
        for col in range(3-row):
            x = (col - (2-row)/2) * .48
            b.beveled_box("metal", (x, .21 + row*.25, 0), (.42,.20,.86), .07, rotation=(0, .08*(col-row), 0))
            b.beveled_box("orange", (x, .22 + row*.25, -.44), (.22,.10,.04), .02)
    return b


def build_fuel():
    b = MeshBuilder("fuel_canister"); add_snow_foot(b, (1.15, .10, 1.08))
    b.beveled_box("red", (0, .56, 0), (.76, 1.02, .62), .16)
    b.beveled_box("dark", (0, 1.05, 0), (.38, .18, .36), .06)
    b.torus("metal", (0, 1.08, 0), .22, .055, 14, 6, rotation=(math.pi/2,0,0), arc=math.pi)
    b.cylinder("yellow", (.22, 1.10, -.18), .08, .22, 10, rotation=(math.pi/2,0,0))
    b.beveled_box("cream", (0, .58, -.33), (.30, .24, .04), .025)
    return b


def build_crate(name="cargo_crate", fish=False):
    b = MeshBuilder(name); add_snow_foot(b, (1.70, .10, 1.36))
    b.beveled_box("wood", (0, .47, 0), (1.42, .82, 1.05), .11)
    for x in (-.62,.62): b.beveled_box("wood_light", (x,.49,0), (.13,.88,1.10), .04)
    for z in (-.47,.47): b.beveled_box("wood_light", (0,.49,z), (1.46,.88,.13), .04)
    b.beveled_box("dark", (0,.91,0), (1.14,.08,.76), .03)
    if fish:
        for x,z,r in [(-.34,-.1,0),(.15,.12,.35),(.38,-.14,-.25)]:
            b.sphere("cyan", (x,1.02,z), (.34,.13,.16), 6, 12, rotation=(0,r,0))
            b.beveled_box("blue", (x-.30*math.cos(r),1.02,z+.30*math.sin(r)), (.20,.05,.25), .025, rotation=(0,r,0))
    else:
        b.beveled_box("yellow", (0,.52,-.56), (.48,.34,.05), .035)
    return b


def build_food():
    b = MeshBuilder("cooked_food_stack"); add_snow_foot(b, (1.65,.10,1.28))
    b.beveled_box("blue", (0,.20,0), (1.34,.18,.96), .08)
    for level in range(3):
        count=4-level
        for i in range(count):
            x=(i-(count-1)/2)*.34
            b.sphere("orange", (x,.40+level*.25,0), (.18,.14,.28), 6, 12, rotation=(0,.12*(i-level),0))
            b.rod_between("yellow", (x,.49+level*.25,-.04),(x,.62+level*.25,-.12),.025,7)
    return b


def build_money():
    b = MeshBuilder("money_stack"); add_snow_foot(b,(1.55,.10,1.24))
    for level in range(4):
        count=3 if level<3 else 2
        for i in range(count):
            x=(i-(count-1)/2)*.42
            b.beveled_box("green",(x,.20+level*.18,0),(.38,.14,.72),.055,rotation=(0,.05*(i-level),0))
            b.beveled_box("cream",(x,.20+level*.18,-.365),(.09,.15,.025),.012)
    for x in (-.44,.44): b.cylinder("yellow",(x,.25,.30),.16,.08,14)
    return b


def asset_specs():
    pads = {"pad_" + k: build_pad("pad_" + k, m) for k, m in {
        "build":"yellow", "upgrade":"orange", "input":"cyan",
        "output":"blue", "stock":"cream", "payment":"green"
    }.items()}
    return {
        "hearth_vessel": build_hearth(),
        "service_counter": build_service_counter(),
        "processing_counter": build_process_counter(),
        **pads,
        "fishing_rack": build_fishing_rack(),
        "intake_machine": build_intake(),
        "cooker_processor": build_cooker(),
        "conveyor_straight": build_conveyor(),
        "defense_platform": build_defense(),
        "wood_stack": build_wood_stack(),
        "stone_stack": build_stone_stack(),
        "metal_stack": build_metal_stack(),
        "fuel_canister": build_fuel(),
        "fish_crate": build_crate("fish_crate", True),
        "cooked_food_stack": build_food(),
        "money_stack": build_money(),
        "cargo_crate": build_crate(),
    }


METADATA = {
    "hearth_vessel": ((2.6,2.25), "T05-R01", "T11", {"input":(0,.45,-1.45),"worker":(1.55,0,0),"fx_heat":(0,1.35,0),"upgrade":(-1.55,0,0)}),
    "service_counter": ((3.45,1.95), "T05-R02", "T17", {"worker":(0,0,1.35),"customer":(0,0,-1.45),"stock":(0,1.3,0),"payment":(1.25,1.3,0)}),
    "processing_counter": ((3.45,1.95), "T05-R02", "T16", {"worker":(0,0,1.35),"input":(-.72,1.8,0),"output":(.72,1.8,0)}),
    "pad_build": ((2.1,2.1), "T05-R03", "T11", {"interaction":(0,.35,0),"icon":(0,.45,0)}),
    "pad_upgrade": ((2.1,2.1), "T05-R03", "T11", {"interaction":(0,.35,0),"icon":(0,.45,0)}),
    "pad_input": ((2.1,2.1), "T05-R03", "T16", {"interaction":(0,.35,0),"transfer":(0,.45,0)}),
    "pad_output": ((2.1,2.1), "T05-R03", "T16", {"interaction":(0,.35,0),"transfer":(0,.45,0)}),
    "pad_stock": ((2.1,2.1), "T05-R03", "T17", {"interaction":(0,.35,0),"stock":(0,.45,0)}),
    "pad_payment": ((2.1,2.1), "T05-R03", "T17", {"interaction":(0,.35,0),"payment":(0,.45,0)}),
    "fishing_rack": ((3.25,1.80), "T05-R04", "T16", {"player":(0,0,-1.15),"water":(0,0,1.15),"output":(0,.8,.5)}),
    "intake_machine": ((2.6,2.4), "T05-R04", "T18", {"input":(0,.8,-1.4),"output":(0,.8,1.4),"upgrade":(-1.65,0,0)}),
    "cooker_processor": ((2.45,2.30), "T05-R05", "T16", {"input":(0,.65,-1.35),"output":(0,.65,1.35),"fx_heat":(0,1.4,0)}),
    "conveyor_straight": ((3.40,1.3), "T05-R05", "T18", {"input":(-1.8,.75,0),"output":(1.8,.75,0)}),
    "defense_platform": ((3.25,3.05), "T05-R06", "T22", {"weapon":(0,1.62,0),"supply":(0,.8,-1.65),"repair":(1.7,0,0)}),
    "wood_stack": ((1.7,1.18), "T05-R07", "T08", {"pickup":(0,.75,0)}),
    "stone_stack": ((1.75,1.38), "T05-R07", "T08", {"pickup":(0,.9,0)}),
    "metal_stack": ((1.75,1.25), "T05-R07", "T08", {"pickup":(0,.8,0)}),
    "fuel_canister": ((1.15,1.08), "T05-R07", "T08", {"pickup":(0,.75,0)}),
    "fish_crate": ((1.7,1.36), "T05-R07", "T16", {"pickup":(0,1.05,0)}),
    "cooked_food_stack": ((1.65,1.28), "T05-R07", "T16", {"pickup":(0,1.0,0)}),
    "money_stack": ((1.55,1.24), "T05-R07", "T17", {"pickup":(0,.95,0)}),
    "cargo_crate": ((1.7,1.36), "T05-R07", "T08", {"pickup":(0,1.0,0)}),
}


ARRANGEMENTS = {
    "camp": [
        ("hearth_vessel", (0,0,.2), 0), ("service_counter", (7.8,0,5.1), 0),
        ("processing_counter", (-7.8,0,5.1), 0), ("pad_upgrade", (-3.0,0,-.8), 0),
        ("pad_stock", (7.8,0,7.2), 0), ("pad_payment", (10.7,0,7.1), 0),
        ("wood_stack", (-10.8,0,7.4), 0), ("stone_stack", (-4.8,0,7.4), 0),
        ("metal_stack", (-10.8,0,4.8), 0), ("fuel_canister", (10.8,0,4.8), 0),
        ("defense_platform", (3.5,0,6.6), 0),
    ],
    "lakeshore": [
        # South-bank bays are split around all three T02/T03 crossing reserves.
        # The spaces are intentional: later bridges retain their full approach
        # corridors while the station line still reads together at T04 scale.
        ("fishing_rack", (-5.6,0,-13.0), 0), ("pad_build", (-6.3,0,-15.1), 0),
        ("intake_machine", (-2.5,0,-13.0), 0), ("pad_input", (-3.8,0,-15.1), 0),
        ("fish_crate", (-1.3,0,-15.1), 0),
        ("conveyor_straight", (4.9,0,-13.0), 0), ("cargo_crate", (7.5,0,-12.8), 0),
        ("pad_output", (4.3,0,-15.1), 0), ("cooker_processor", (7.1,0,-15.0), 0),
        ("cooked_food_stack", (12.6,0,-14.6), 0),
    ],
}


def pack_glb(builder: MeshBuilder, path: Path):
    blob = bytearray(); views=[]; accessors=[]; primitives=[]; materials=[]
    used = list(builder.surfaces)
    for key in used:
        color, metallic, rough = MATERIALS[key]
        materials.append({
            "name":"HL_"+key,
            "pbrMetallicRoughness":{"baseColorFactor":color,"metallicFactor":metallic,"roughnessFactor":rough},
            "doubleSided":False,
        })
    def add_view(data: bytes, target: int):
        while len(blob) % 4: blob.append(0)
        offset=len(blob); blob.extend(data)
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(data),"target":target})
        return len(views)-1
    for material_index, key in enumerate(used):
        surface=builder.surfaces[key]
        pos_data=b"".join(struct.pack("<3f",*p) for p in surface.positions)
        nor_data=b"".join(struct.pack("<3f",*n) for n in surface.normals)
        idx_data=b"".join(struct.pack("<I",i) for i in surface.indices)
        p_view=add_view(pos_data,34962); n_view=add_view(nor_data,34962); i_view=add_view(idx_data,34963)
        mins=[min(p[i] for p in surface.positions) for i in range(3)]
        maxs=[max(p[i] for p in surface.positions) for i in range(3)]
        p_acc=len(accessors); accessors.append({"bufferView":p_view,"componentType":5126,"count":len(surface.positions),"type":"VEC3","min":mins,"max":maxs})
        n_acc=len(accessors); accessors.append({"bufferView":n_view,"componentType":5126,"count":len(surface.normals),"type":"VEC3"})
        i_acc=len(accessors); accessors.append({"bufferView":i_view,"componentType":5125,"count":len(surface.indices),"type":"SCALAR"})
        primitives.append({"attributes":{"POSITION":p_acc,"NORMAL":n_acc},"indices":i_acc,"material":material_index,"mode":4})
    doc={
        "asset":{"version":"2.0","generator":"Havenline T05 deterministic sculptor v1"},
        "scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"name":builder.name,"mesh":0}],
        "meshes":[{"name":builder.name,"primitives":primitives}],"materials":materials,
        "accessors":accessors,"bufferViews":views,"buffers":[{"byteLength":len(blob)}],
    }
    encoded=json.dumps(doc,separators=(",",":"),sort_keys=True).encode()
    while len(encoded)%4: encoded+=b" "
    while len(blob)%4: blob.append(0)
    total=12+8+len(encoded)+8+len(blob)
    data=struct.pack("<4sII",b"glTF",2,total)+struct.pack("<I4s",len(encoded),b"JSON")+encoded+struct.pack("<I4s",len(blob),b"BIN\0")+blob
    path.write_bytes(data)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assets=asset_specs(); entries=[]
    expected_files={asset_id+".glb" for asset_id in assets}
    for stale_path in OUT.glob("*.glb"):
        if stale_path.name not in expected_files:
            stale_path.unlink()
    for asset_id in sorted(assets):
        builder=assets[asset_id]; path=OUT/(asset_id+".glb"); pack_glb(builder,path)
        footprint, requirement, later_task, sockets=METADATA[asset_id]
        entries.append({
            "id":asset_id,"asset":"res://assets/stations_v2/"+path.name,
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "requirement":requirement,"later_task":later_task,
            "footprint":[footprint[0],footprint[1]],"clearance":0.55,
            "sockets":{name:list(value) for name,value in sockets.items()},
            "triangles":builder.triangle_count(),"materials":sorted(builder.surfaces),
        })
    catalog={
        "schema_version":1,"authority_id":"T05-station-kit-v1","generator":"tools/havenline/task05/generate_station_kit.py",
        "art_language":"bright sculpted winter production kit; shared blue/orange/yellow machinery with warm timber and snow contact",
        "requirements":[f"T05-R{i:02d}" for i in range(1,13)],
        "entries":entries,
        "arrangements":{name:[{"id":i,"position":list(p),"rotation_y":r} for i,p,r in rows] for name,rows in ARRANGEMENTS.items()},
        "performance_contract":{"triangles_max":180000,"draw_calls_max":48,"visible_materials_max":12,"texture_memory_mib_max":96,"storage_delta_mib_max":15,"active_physics":0,"skeletons":0,"animations":0,"population":0},
        "runtime_logic_included":False,"visual_approval_claimed":False,"physical_4k60_certified":False,
    }
    catalog_path=OUT/"catalog.json"
    catalog_path.write_text(json.dumps(catalog,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"assets":len(entries),"triangles":sum(x["triangles"] for x in entries),"catalog":str(catalog_path.relative_to(ROOT))},indent=2))


if __name__=="__main__":
    main()
