"""T05-only authored timber relief and irregular snow deposition.

Decorate construction members in their local axis before their existing rotation.
The immutable R01 hearth is excluded. No material slot or gameplay field is added.
"""
import math
import legacy_station_kit_v1 as legacy

BASE_BUILDER = legacy.MeshBuilder


class SurfaceReliefBuilder(BASE_BUILDER):
    pigment = 1.0

    def triangles(self, material, vertices, normals, indices, center=(0, 0, 0), rotation=(0, 0, 0)):
        start = len(self._surface(material).positions)
        super().triangles(material, vertices, normals, indices, center, rotation)
        if not hasattr(self, "vertex_pigments"):
            self.vertex_pigments = {}
        if self.pigment != 1.0:
            self.vertex_pigments.setdefault(material, {}).update(
                (i, self.pigment) for i in range(start, len(self.surfaces[material].positions)))

    def _carved_board(self, material, center, size, bevel, rotation):
        # Carve the board's own face. No overlaid strips, thin side walls or
        # detached grains can generate projected dotted shadow rows.
        axis = max(range(3), key=lambda i: size[i])
        half = tuple(value * .5 for value in size)
        bevel = max(.001, min(bevel, min(half) * .46))
        inner = tuple(value - bevel for value in half)
        vertices, normals, indices, shades = [], [], [], []
        def profile(p, fixed, sign):
            across = next(i for i in range(3) if i not in (axis, fixed))
            t, u = p[axis] / inner[axis], p[across] / inner[across]
            envelope = max(0., 1 - t * t) * max(0., 1 - u * u)
            wave = .5 + .5 * math.cos(u * 5.3 + .65 * math.sin(t * 2.3 + sign))
            depth = min(.0045, size[fixed] * .035) * envelope * wave
            shade = 1 - .15 * envelope * wave
            return depth, shade
        for fixed, ua, va, sign in ((0, 1, 2, 1), (0, 1, 2, -1),
                                     (1, 0, 2, 1), (1, 0, 2, -1),
                                     (2, 0, 1, 1), (2, 0, 1, -1)):
            coordinates = lambda a: ([-half[a], -inner[a], inner[a], half[a]] if fixed == axis else [-half[a], -inner[a], -.4 * inner[a], .4 * inner[a], inner[a], half[a]])
            us, vs = coordinates(ua), coordinates(va)
            grid = []
            for vv in vs:
                row = []
                for uu in us:
                    p = [0., 0., 0.];p[fixed] = sign * half[fixed];p[ua], p[va] = uu, vv
                    q = [max(-inner[i], min(inner[i], p[i])) for i in range(3)]
                    n = legacy.vnorm(legacy.vsub(p, q))
                    pos = list(legacy.vadd(q, legacy.vmul(n, bevel)))
                    shade = 1.
                    if fixed != axis and abs(uu) < inner[ua] and abs(vv) < inner[va]:
                        depth, shade = profile(p, fixed, sign)
                        pos[fixed] -= sign * depth
                        normal = [0., 0., 0.];normal[fixed] = sign
                        for tangent in (ua, va):
                            eps = .0001
                            a, b = list(p), list(p);a[tangent] += eps;b[tangent] -= eps
                            normal[tangent] = (profile(a, fixed, sign)[0] - profile(b, fixed, sign)[0]) / (2 * eps)
                        n = legacy.vnorm(normal)
                    row.append(len(vertices));vertices.append(pos);normals.append(n);shades.append(shade)
                grid.append(row)
            for v in range(len(vs) - 1):
                for u in range(len(us) - 1):
                    a, b, c, d = grid[v][u], grid[v][u+1], grid[v+1][u+1], grid[v+1][u]
                    indices.extend((a, b, c, a, c, d))
        start = len(self._surface(material).positions)
        self.triangles(material, vertices, normals, indices, center, rotation)
        self.vertex_pigments.setdefault(material, {}).update((start+i, shade) for i, shade in enumerate(shades) if shade != 1.)

    def beveled_box(self, material, center, size, bevel=.08, rotation=(0, 0, 0)):
        if self.name == "hearth_vessel":
            return super().beveled_box(material, center, size, bevel, rotation)
        if material == "snow":
            # Closed asymmetric accumulation. Elliptical scallops and crowned
            # normals replace flat rectangular snow plates on rails/crates/pads.
            rx, rz = size[0] * .5 / 1.145, size[2] * .5 / 1.145
            ry = max(size[1] * .62, min(.095, min(rx, rz) * .34))
            lower_ry = min(ry, size[1] * .5 / 1.1)
            vertices, normals, indices = [], [], []
            rings, segments = 7, 14
            for ring in range(rings + 1):
                phi = math.pi * ring / rings
                for i in range(segments):
                    theta = math.tau * i / segments
                    wobble = 1 + .10 * math.sin(theta * 3 + .7) + .045 * math.cos(theta * 5)
                    u = (math.cos(theta) * math.sin(phi), math.cos(phi), math.sin(theta) * math.sin(phi))
                    vertical_radius = ry if u[1] >= 0 else lower_ry
                    vertices.append((u[0] * rx * wobble, u[1] * vertical_radius * (1 + .10 * math.sin(theta) * math.sin(phi)), u[2] * rz * wobble))
                    normals.append(legacy.vnorm((u[0] / rx, u[1] / vertical_radius, u[2] / rz)))
            for ring in range(rings):
                for i in range(segments):
                    j = (i + 1) % segments
                    a, b = ring * segments + i, ring * segments + j
                    c, d = (ring + 1) * segments + j, (ring + 1) * segments + i
                    indices.extend((a, c, b, a, d, c))
            return self.triangles(material, vertices, normals, indices, center, rotation)
        if material in ("wood", "wood_light") and max(size) >= .58 and max(size) / max(.01, min(size)) >= 2.2:
            return self._carved_board(material, center, size, bevel, rotation)
        return super().beveled_box(material, center, size, bevel, rotation)


def install():
    legacy.MeshBuilder = SurfaceReliefBuilder
