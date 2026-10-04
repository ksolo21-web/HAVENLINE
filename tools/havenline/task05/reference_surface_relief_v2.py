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

    def _grain(self, material, center, size, rotation):
        axis = max(range(3), key=lambda i: size[i])
        length = size[axis]
        if length < .58 or length / max(.01, min(size)) < 2.2:
            return
        # Broad tapered shallow carvings stay continuous at mobile projection.
        # Thin buried rods previously became dotted high-contrast pixels.
        across = 2 if axis in (0, 1) else 0
        face = 1 if axis != 1 else 0
        self.pigment = .78
        for line in (-1, 1):
            vertices, normals, indices = [], [], []
            stations = 5
            width = min(.023, size[across] * .10)
            for layer in (0, 1):
                for j in range(stations):
                    t = j / (stations - 1)
                    taper = .12 + .88 * math.sin(math.pi * t)
                    for edge in (-1, 1):
                        p = [0., 0., 0.]
                        p[axis] = length * (-.35 + .69 * t) + line * length * .025
                        p[face] = size[face] * .5 + (.0018 if layer else -.002)
                        p[across] = line * size[across] * .19 + size[across] * .035 * math.sin(t * 5 + line) + edge * width * taper
                        vertices.append(p)
                        n = [0., 0., 0.]; n[face] = 1 if layer else -1
                        normals.append(n)
            count = stations * 2
            def quad(a, b, c, d):
                indices.extend((a, b, c, a, c, d))
            for off in (0, count):
                for j in range(stations - 1):
                    a = off + j * 2
                    quad(a, a + 2, a + 3, a + 1)
            perimeter = list(range(0, count, 2)) + list(range(count - 1, 0, -2))
            for a, b in zip(perimeter, perimeter[1:] + perimeter[:1]):
                pa, pb = vertices[a], vertices[b]
                n = [0., 0., 0.]
                n[axis] = (pa[axis] + pb[axis]) / length
                n[across] = (pa[across] + pb[across]) / size[across] - line * .19
                k = len(vertices)
                vertices.extend((vertices[a], vertices[b], vertices[b + count], vertices[a + count]))
                normals.extend((n, n, n, n))
                quad(k, k + 1, k + 2, k + 3)
            self.triangles(material, vertices, normals, indices, center, rotation)
        self.pigment = 1.0

    def beveled_box(self, material, center, size, bevel=.08, rotation=(0, 0, 0)):
        if self.name == "hearth_vessel":
            return super().beveled_box(material, center, size, bevel, rotation)
        if material == "snow":
            # Closed asymmetric accumulation. Elliptical scallops and crowned
            # normals replace flat rectangular snow plates on rails/crates/pads.
            rx, rz = size[0] * .52, size[2] * .53
            ry = max(size[1] * .62, min(.095, min(rx, rz) * .34))
            vertices, normals, indices = [], [], []
            rings, segments = 7, 14
            for ring in range(rings + 1):
                phi = math.pi * ring / rings
                for i in range(segments):
                    theta = math.tau * i / segments
                    wobble = 1 + .10 * math.sin(theta * 3 + .7) + .045 * math.cos(theta * 5)
                    u = (math.cos(theta) * math.sin(phi), math.cos(phi), math.sin(theta) * math.sin(phi))
                    vertices.append((u[0] * rx * wobble, u[1] * ry * (1 + .10 * math.sin(theta) * math.sin(phi)), u[2] * rz * wobble))
                    normals.append(legacy.vnorm((u[0] / rx, u[1] / ry, u[2] / rz)))
            for ring in range(rings):
                for i in range(segments):
                    j = (i + 1) % segments
                    a, b = ring * segments + i, ring * segments + j
                    c, d = (ring + 1) * segments + j, (ring + 1) * segments + i
                    indices.extend((a, c, b, a, d, c))
            return self.triangles(material, vertices, normals, indices, center, rotation)
        super().beveled_box(material, center, size, bevel, rotation)
        if material in ("wood", "wood_light"):
            self._grain(material, center, size, rotation)


def install():
    legacy.MeshBuilder = SurfaceReliefBuilder
