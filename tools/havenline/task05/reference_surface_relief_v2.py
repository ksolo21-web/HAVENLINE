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
        # Grain follows the construction member, including vertical posts and
        # rotated diagonal bracing. Lines sit partially inside the wood face.
        across = 2 if axis in (0, 1) else 0
        face = 1 if axis != 1 else 0
        radius = min(.007, min(size) * .050)
        matrix = legacy.rotation_matrix(*rotation)
        def world(p):
            return legacy.vadd(legacy.mat_vec(matrix, p), center)
        self.pigment = .42
        for line in (-1, 1):
            points = []
            for j in range(5):
                t = j / 4
                p = [0., 0., 0.]
                p[axis] = length * (-.36 + .72 * t)
                p[face] = size[face] * .5 - radius * .25
                p[across] = line * size[across] * .18 + size[across] * .032 * math.sin(t * 7 + line)
                points.append(world(p))
            for a, b in zip(points, points[1:]):
                super().rod_between(material, a, b, radius, 5)
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
